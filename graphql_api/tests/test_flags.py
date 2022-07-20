from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from codecov_auth.tests.factories import OwnerFactory
from core.tests.factories import CommitFactory, RepositoryFactory
from reports.tests.factories import RepositoryFlagFactory
from timeseries.tests.factories import MeasurementFactory

from .helper import GraphQLTestHelper

query_flags = """
query Flags(
    $org: String!
    $repo: String!
    $measurementsAfter: DateTime!
    $measurementsBefore: DateTime!
) {
    owner(username: $org) {
        repository(name: $repo) {
            flags {
                edges {
                    node {
                        ...FlagFragment
                    }
                }
            }
        }
    }
}

fragment FlagFragment on Flag {
    name
    percentCovered
    percentChange
    measurements(
        interval: INTERVAL_1_DAY
        after: $measurementsAfter,
        before: $measurementsBefore
    ) {
        timestamp
        avg
        min
        max
    }
}
"""


@pytest.mark.skipif(
    not settings.TIMESERIES_ENABLED, reason="requires timeseries data storage"
)
class TestFlags(GraphQLTestHelper, TransactionTestCase):
    databases = {"default", "timeseries"}

    def setUp(self):
        self.org = OwnerFactory()
        self.repo = RepositoryFactory(author=self.org, private=False)
        self.commit = CommitFactory(repository=self.repo)

    def test_fetch_flags_no_measurements(self):
        flag1 = RepositoryFlagFactory(repository=self.repo, flag_name="flag1")
        flag2 = RepositoryFlagFactory(repository=self.repo, flag_name="flag2")
        variables = {
            "org": self.org.username,
            "repo": self.repo.name,
            "measurementsAfter": timezone.datetime(2022, 1, 1),
            "measurementsBefore": timezone.datetime(2022, 12, 31),
        }
        data = self.gql_request(query_flags, variables=variables)
        assert data == {
            "owner": {
                "repository": {
                    "flags": {
                        "edges": [
                            {
                                "node": {
                                    "name": "flag1",
                                    "percentCovered": None,
                                    "percentChange": None,
                                    "measurements": [],
                                }
                            },
                            {
                                "node": {
                                    "name": "flag2",
                                    "percentCovered": None,
                                    "percentChange": None,
                                    "measurements": [],
                                }
                            },
                        ]
                    }
                }
            }
        }

    @override_settings(TIMESERIES_ENABLED=False)
    def test_fetch_flags_timeseries_not_enabled(self):
        flag1 = RepositoryFlagFactory(repository=self.repo, flag_name="flag1")
        flag2 = RepositoryFlagFactory(repository=self.repo, flag_name="flag2")
        variables = {
            "org": self.org.username,
            "repo": self.repo.name,
            "measurementsAfter": timezone.datetime(2022, 1, 1),
            "measurementsBefore": timezone.datetime(2022, 12, 31),
        }
        data = self.gql_request(query_flags, variables=variables)
        assert data == {
            "owner": {
                "repository": {
                    "flags": {
                        "edges": [
                            {
                                "node": {
                                    "name": "flag1",
                                    "percentCovered": None,
                                    "percentChange": None,
                                    "measurements": [],
                                }
                            },
                            {
                                "node": {
                                    "name": "flag2",
                                    "percentCovered": None,
                                    "percentChange": None,
                                    "measurements": [],
                                }
                            },
                        ]
                    }
                }
            }
        }

    def test_fetch_flags_with_measurements(self):
        flag1 = RepositoryFlagFactory(repository=self.repo, flag_name="flag1")
        flag2 = RepositoryFlagFactory(repository=self.repo, flag_name="flag2")
        MeasurementFactory(
            name="flag_coverage",
            owner_id=self.org.pk,
            repo_id=self.repo.pk,
            branch="main",
            flag_id=flag1.pk,
            commit_sha=self.commit.pk,
            timestamp="2022-06-21T00:00:00",
            value=75.0,
        )
        MeasurementFactory(
            name="flag_coverage",
            owner_id=self.org.pk,
            repo_id=self.repo.pk,
            branch="main",
            flag_id=flag1.pk,
            commit_sha=self.commit.pk,
            timestamp="2022-06-22T00:00:00",
            value=75.0,
        )
        MeasurementFactory(
            name="flag_coverage",
            owner_id=self.org.pk,
            repo_id=self.repo.pk,
            branch="main",
            flag_id=flag1.pk,
            commit_sha=self.commit.pk,
            timestamp="2022-06-22T01:00:00",
            value=85.0,
        )
        MeasurementFactory(
            name="flag_coverage",
            owner_id=self.org.pk,
            repo_id=self.repo.pk,
            branch="main",
            flag_id=flag2.pk,
            commit_sha=self.commit.pk,
            timestamp="2022-06-21T00:00:00",
            value=85.0,
        )
        MeasurementFactory(
            name="flag_coverage",
            owner_id=self.org.pk,
            repo_id=self.repo.pk,
            branch="main",
            flag_id=flag2.pk,
            commit_sha=self.commit.pk,
            timestamp="2022-06-22T00:00:00",
            value=95.0,
        )
        MeasurementFactory(
            name="flag_coverage",
            owner_id=self.org.pk,
            repo_id=self.repo.pk,
            branch="main",
            flag_id=flag2.pk,
            commit_sha=self.commit.pk,
            timestamp="2022-06-22T01:00:00",
            value=85.0,
        )
        variables = {
            "org": self.org.username,
            "repo": self.repo.name,
            "measurementsAfter": timezone.datetime(2022, 6, 20),
            "measurementsBefore": timezone.datetime(2022, 6, 23),
        }
        data = self.gql_request(query_flags, variables=variables)
        assert data == {
            "owner": {
                "repository": {
                    "flags": {
                        "edges": [
                            {
                                "node": {
                                    "name": "flag1",
                                    "percentCovered": 80.0,
                                    "percentChange": 6.666666666666665,
                                    "measurements": [
                                        {
                                            "timestamp": "2022-06-20T00:00:00+00:00",
                                            "avg": None,
                                            "min": None,
                                            "max": None,
                                        },
                                        {
                                            "timestamp": "2022-06-21T00:00:00+00:00",
                                            "avg": 75.0,
                                            "min": 75.0,
                                            "max": 75.0,
                                        },
                                        {
                                            "timestamp": "2022-06-22T00:00:00+00:00",
                                            "avg": 80.0,
                                            "min": 75.0,
                                            "max": 85.0,
                                        },
                                        {
                                            "timestamp": "2022-06-23T00:00:00+00:00",
                                            "avg": None,
                                            "min": None,
                                            "max": None,
                                        },
                                    ],
                                }
                            },
                            {
                                "node": {
                                    "name": "flag2",
                                    "percentCovered": 90.0,
                                    "percentChange": 5.882352941176472,
                                    "measurements": [
                                        {
                                            "timestamp": "2022-06-20T00:00:00+00:00",
                                            "avg": None,
                                            "min": None,
                                            "max": None,
                                        },
                                        {
                                            "timestamp": "2022-06-21T00:00:00+00:00",
                                            "avg": 85.0,
                                            "min": 85.0,
                                            "max": 85.0,
                                        },
                                        {
                                            "timestamp": "2022-06-22T00:00:00+00:00",
                                            "avg": 90.0,
                                            "min": 85.0,
                                            "max": 95.0,
                                        },
                                        {
                                            "timestamp": "2022-06-23T00:00:00+00:00",
                                            "avg": None,
                                            "min": None,
                                            "max": None,
                                        },
                                    ],
                                }
                            },
                        ]
                    }
                }
            }
        }

    def test_fetch_flags_without_measurements(self):
        query = """
            query Flags(
                $org: String!
                $repo: String!
            ) {
                owner(username: $org) {
                    repository(name: $repo) {
                        flags {
                            edges {
                                node {
                                    name
                                    percentCovered
                                    percentChange
                                }
                            }
                        }
                    }
                }
            }
        """
        RepositoryFlagFactory(repository=self.repo, flag_name="flag1")
        RepositoryFlagFactory(repository=self.repo, flag_name="flag2")
        variables = {
            "org": self.org.username,
            "repo": self.repo.name,
        }
        data = self.gql_request(query, variables=variables)
        assert data == {
            "owner": {
                "repository": {
                    "flags": {
                        "edges": [
                            {
                                "node": {
                                    "name": "flag1",
                                    "percentCovered": None,
                                    "percentChange": None,
                                }
                            },
                            {
                                "node": {
                                    "name": "flag2",
                                    "percentCovered": None,
                                    "percentChange": None,
                                }
                            },
                        ]
                    }
                }
            }
        }

    def test_fetch_flags_term_filter(self):
        query = """
            query Flags(
                $org: String!
                $repo: String!
                $filters: FlagSetFilters!
            ) {
                owner(username: $org) {
                    repository(name: $repo) {
                        flags(filters: $filters) {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        """
        RepositoryFlagFactory(repository=self.repo, flag_name="flag1")
        RepositoryFlagFactory(repository=self.repo, flag_name="flag2")
        variables = {
            "org": self.org.username,
            "repo": self.repo.name,
            "filters": {"term": "ag1"},
        }
        data = self.gql_request(query, variables=variables)
        assert data == {
            "owner": {
                "repository": {
                    "flags": {
                        "edges": [
                            {
                                "node": {
                                    "name": "flag1",
                                }
                            },
                        ]
                    }
                }
            }
        }

    def test_fetch_flags_ordering_direction(self):
        query = """
            query Flags(
                $org: String!
                $repo: String!
            ) {
                owner(username: $org) {
                    repository(name: $repo) {
                        flags(orderingDirection: DESC) {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        """
        RepositoryFlagFactory(repository=self.repo, flag_name="flag1")
        RepositoryFlagFactory(repository=self.repo, flag_name="flag2")
        variables = {
            "org": self.org.username,
            "repo": self.repo.name,
        }
        data = self.gql_request(query, variables=variables)
        assert data == {
            "owner": {
                "repository": {
                    "flags": {
                        "edges": [
                            {
                                "node": {
                                    "name": "flag2",
                                }
                            },
                            {
                                "node": {
                                    "name": "flag1",
                                }
                            },
                        ]
                    }
                }
            }
        }

    @patch("timeseries.models.MeasurementSummary.agg_by")
    def test_fetch_flags_empty_lookahead(self, agg_by):
        query = """
            query Flags(
                $org: String!
                $repo: String!
            ) {
                owner(username: $org) {
                    repository(name: $repo) {
                        flags {
                            __typename
                        }
                    }
                }
            }
        """
        RepositoryFlagFactory(repository=self.repo, flag_name="flag1")
        RepositoryFlagFactory(repository=self.repo, flag_name="flag2")
        variables = {
            "org": self.org.username,
            "repo": self.repo.name,
        }
        self.gql_request(query, variables=variables)
        assert agg_by.call_count == 0
