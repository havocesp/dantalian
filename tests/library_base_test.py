"""
This module contains unit tests for dantalian.library.base
"""

import unittest
import tempfile
import shutil
import os

from . import testlib
from dantalian.library import base as library


class TestLibraryBase(testlib.ExtendedTestCase):

    def setUp(self):
        self._olddir = os.getcwd()
        self.root = tempfile.mkdtemp()
        os.chdir(self.root)
        os.makedirs('A')
        os.makedirs('B')
        os.mknod(os.path.join('A', 'a'))
        os.mknod(os.path.join('A', 'b'))
        os.link(os.path.join('A', 'b'), os.path.join('B', 'b'))

    def tearDown(self):
        shutil.rmtree(self.root)
        os.chdir(self._olddir)

    def test_tag(self):
        library.tag(os.path.join('A', 'a'), 'B')
        self.assertSameFile(os.path.join('A', 'a'), os.path.join('B', 'a'))

    def test_untag(self):
        library.untag(os.path.join('A', 'b'), 'B')
        self.assertNotSameFile(os.path.join('A', 'b'), os.path.join('B', 'b'))


class TestLibraryBaseQuery(testlib.ExtendedTestCase):

    def setUp(self):
        self._olddir = os.getcwd()
        self.root = tempfile.mkdtemp()
        os.chdir(self.root)
        os.makedirs('A')
        os.makedirs('B')
        os.makedirs('C')
        os.mknod(os.path.join('A', 'a'))
        os.mknod(os.path.join('A', 'b'))
        os.mknod(os.path.join('A', 'c'))
        os.mknod(os.path.join('C', 'd'))
        os.link(os.path.join('A', 'b'), os.path.join('B', 'b'))
        os.link(os.path.join('A', 'c'), os.path.join('B', 'c'))
        os.link(os.path.join('A', 'c'), os.path.join('C', 'c'))

    def tearDown(self):
        shutil.rmtree(self.root)
        os.chdir(self._olddir)

    def test_and(self):
        results = library.search(
            library.AndNode(
                [library.DirNode('A'),
                 library.DirNode('B'),
                 library.DirNode('C')]
            )
        )
        self.assertListEqual(
            results,
            [os.path.join('A', 'c')],
        )

    def test_or(self):
        results = library.search(
            library.OrNode(
                [library.DirNode('A'),
                 library.DirNode('B'),
                 library.DirNode('C')]
            )
        )
        self.assertListEqual(
            sorted(results),
            sorted([os.path.join('A', 'a'),
                    os.path.join('A', 'b'),
                    os.path.join('A', 'c'),
                    os.path.join('C', 'd')]),
        )


class TestLibraryBaseParsing(testlib.ExtendedTestCase):

    def test_parse_and(self):
        tree = library.parse_query("AND A B C )")
        self.assertSameTree(tree, library.AndNode(
            [library.DirNode("A"),
             library.DirNode("B"),
             library.DirNode("C")]))

    def test_parse_or(self):
        tree = library.parse_query("OR A B C )")
        self.assertSameTree(tree, library.OrNode(
            [library.DirNode("A"),
             library.DirNode("B"),
             library.DirNode("C")]))

    def test_parse_and_escape(self):
        tree = library.parse_query(r"AND '\AND' '\\AND' '\\\AND' )")
        self.assertSameTree(tree, library.AndNode(
            [library.DirNode(r'AND'),
             library.DirNode(r'\AND'),
             library.DirNode(r'\\AND')]))

    def test_parse_and_or(self):
        tree = library.parse_query("AND A B C OR spam eggs ) )")
        self.assertSameTree(tree, library.AndNode(
            [library.DirNode("A"),
             library.DirNode("B"),
             library.DirNode("C"),
             library.OrNode(
                 [library.DirNode('spam'),
                  library.DirNode('eggs')])
            ]))