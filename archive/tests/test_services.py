from unittest.mock import patch
from pathlib import Path

from archive.services import build_report, ArchiveService, MinioEndpoints
from core.tests.factories import CommitFactory

current_file = Path(__file__)


def test_report_generator():
    data = {
        'chunks': '{}\n[1, null, [[0, 1]]]\n\n\n[1, null, [[0, 1]]]\n[0, null, [[0, 0]]]\n<<<<< end_of_chunk >>>>>\n{}\n[1, null, [[0, 1]]]\n\n\n[1, null, [[0, 1]]]\n[1, null, [[0, 1]]]\n\n\n[1, null, [[0, 1]]]\n[1, null, [[0, 1]]]\n\n\n[1, null, [[0, 1]]]\n[1, null, [[0, 1]]]\n<<<<< end_of_chunk >>>>>\n{}\n[1, null, [[0, 1]]]\n[1, null, [[0, 1]]]\n\n\n[1, null, [[0, 1]]]\n[0, null, [[0, 0]]]\n\n\n[1, null, [[0, 1]]]\n[1, null, [[0, 1]]]\n[1, null, [[0, 1]]]\n[1, null, [[0, 1]]]\n\n\n[1, null, [[0, 1]]]\n[0, null, [[0, 0]]]',
        'files': {
            'awesome/__init__.py': [
                2,
                [0, 10, 8, 2, 0, '80.00000', 0, 0, 0, 0, 0, 0, 0],
                [
                    [0, 10, 8, 2, 0, '80.00000', 0, 0, 0, 0, 0, 0, 0]
                ],
                [
                    0, 2, 1, 1, 0, '50.00000', 0, 0, 0, 0, 0, 0, 0
                ]
            ],
            'tests/__init__.py': [
                0,
                [
                    0, 3, 2, 1, 0, '66.66667', 0, 0, 0, 0, 0, 0, 0
                ],
                [
                    [0, 3, 2, 1, 0, '66.66667', 0, 0, 0, 0, 0, 0, 0]
                ],
                None
            ],
            'tests/test_sample.py': [
                1,
                [0, 7, 7, 0, 0, '100', 0, 0, 0, 0, 0, 0, 0],
                [
                    [0, 7, 7, 0, 0, '100', 0, 0, 0, 0, 0, 0, 0]
                ],
                None
            ]
        },
        'sessions': {
            '0': {
                'N': None,
                'a': 'v4/raw/2019-01-10/839C9EAF1A3F1CD45AA08DF5F791461F/abf6d4df662c47e32460020ab14abf9303581429/9ccc55a1-8b41-4bb1-a946-ee7a33a7fb56.txt',
                'c': None,
                'd': 1547084427,
                'e': None,
                'f': None,
                'j': None,
                'n': None,
                'p': None,
                't': [
                    3, 20, 17, 3, 0, '85.00000', 0, 0, 0, 0, 0, 0, 0
                ],
                '': None
            }
        },
        'totals': {
            'C': 0,
            'M': 0,
            'N': 0,
            'b': 0,
            'c': '85.00000',
            'd': 0,
            'diff': [1, 2, 1, 1, 0, '50.00000', 0, 0, 0, 0, 0, 0, 0],
            'f': 3,
            'h': 17,
            'm': 3,
            'n': 20,
            'p': 0,
            's': 1
        }
    }

    res = build_report(**data)
    assert len(res._chunks) == 3


def test_build_report_from_commit(db):
    with patch('archive.services.download_content') as mocked:
        f = open(current_file.parent / 'samples' / 'chunks.txt', 'r')
        mocked.return_value = f.read()
        commit = CommitFactory.create(message='aaaaa', commitid='abf6d4d')
        res = ArchiveService().build_report_from_commit(commit)
        assert len(res._chunks) == 3
        assert len(res.files) == 3
        file_1, file_2, file_3 = sorted(res.file_reports(), key=lambda x: x.name)
        assert file_1.name == 'awesome/__init__.py'
        assert file_2.name == 'tests/__init__.py'
        assert file_3.name == 'tests/test_sample.py'
        mocked.assert_called_with(
                MinioEndpoints.chunks,
                commitid='abf6d4d',
                repo_hash='4434BC2A2EC4FCA57F77B473D83F928C',
                version='v4'
            )
