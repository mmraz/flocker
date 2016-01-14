# Copyright ClusterHQ Inc.  See LICENSE file for details.

from hypothesis import given
from testtools.matchers import (
    AfterPreprocessing,
    DirExists,
    Equals,
    FileExists,
    Is,
    Not,
    PathExists,
)


from .. import TestCase
from ..strategies import paths
from ..matchers import (
    dir_exists,
    file_exists,
    path_exists,
)


def is_equivalent_mismatch(expected):
    """
    Matches another mismatch.

    :param Optional[Mismatch] expected: If None, then match None,
        otherwise, match a mismatch that has the same description and details.
    :rtype: Matcher
    """
    def to_dict(mismatch):
        return {
            'details': mismatch.get_details(),
            'description': mismatch.describe(),
        }
    if expected is None:
        return Is(None)
    # XXX: This should really be a standard combinator.
    return AfterPreprocessing(
        to_dict, Equals(to_dict(expected)), annotate=False)


class PathExistsTests(TestCase):
    """
    Tests for :py:func:`path_exists`.
    """

    def test_does_not_exist(self):
        """
        If the path does not exist, path_exists does not match.
        """
        path = self.make_temporary_path()
        self.assertThat(path, Not(path_exists()))

    def test_file_exists(self):
        """
        If there is a file at path, path_exists matches.
        """
        path = self.make_temporary_path()
        path.setContent('foo')
        self.assertThat(path, path_exists())

    def test_dir_exists(self):
        """
        If there is a directory at path, path_exists matches.
        """
        path = self.make_temporary_path()
        path.makedirs()
        self.assertThat(path, path_exists())

    @given(paths)
    def test_equivalent_to_standard_path_exists(self, path):
        """
        path_exists is to FilePaths what PathExists is to normal paths.
        """
        self.assertThat(
            path_exists().match(path),
            is_equivalent_mismatch(PathExists().match(path.path)),
        )


class DirExistsTests(TestCase):
    """
    Tests for :py:func:`dir_exists`.
    """

    def test_does_not_exist(self):
        """
        If the path does not exist, dir_exists does not match.
        """
        path = self.make_temporary_path()
        self.assertThat(path, Not(dir_exists()))

    def test_file_exists(self):
        """
        If there is a file at path, dir_exists does not match.
        """
        path = self.make_temporary_path()
        path.setContent('foo')
        self.assertThat(path, Not(dir_exists()))

    def test_dir_exists(self):
        """
        If there is a directory at path, dir_exists matches.
        """
        path = self.make_temporary_path()
        path.makedirs()
        self.assertThat(path, dir_exists())

    @given(paths)
    def test_equivalent_to_standard_dir_exists(self, path):
        """
        dir_exists is to FilePaths what DirExists is to normal paths.
        """
        self.assertThat(
            dir_exists().match(path),
            is_equivalent_mismatch(DirExists().match(path.path)),
        )


class FileExistsTests(TestCase):
    """
    Tests for :py:func:`file_exists`.
    """

    def test_does_not_exist(self):
        """
        If the path does not exist, file_exists does not match.
        """
        path = self.make_temporary_path()
        self.assertThat(path, Not(file_exists()))

    def test_file_exists(self):
        """
        If there is a file at path, file_exists matches.
        """
        path = self.make_temporary_path()
        path.setContent('foo')
        self.assertThat(path, file_exists())

    def test_dir_exists(self):
        """
        If there is a directory at path, file_exists does not match.
        """
        path = self.make_temporary_directory()
        self.assertThat(path, Not(file_exists()))

    @given(paths)
    def test_equivalent_to_standard_file_exists(self, path):
        """
        file_exists is to FilePaths what FileExists is to normal paths.
        """
        self.assertThat(
            file_exists().match(path),
            is_equivalent_mismatch(FileExists().match(path.path)),
        )
