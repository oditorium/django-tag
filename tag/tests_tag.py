"""
testing code for `tag.py`

Copyright (c) Stefan LOESCH, oditorium 2016. All Rights Reserved.
Licensed under the MIT License <https://opensource.org/licenses/MIT>.
"""
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse_lazy, reverse
#from Presmo.tools import ignore_failing_tests, ignore_long_tests

from django.db.utils import IntegrityError


from .models import *
from .models.tag import _Dummy

class TestTags(TestCase):
    """
    testing the tags themselves
    """

    ####################################################################
    ## TEST BASE
    def test_base(s):
        """test the TagBase model"""
        with s.assertRaises( NotImplementedError ): TagBase().tag

    ####################################################################
    ## TEST ROOT
    def test_root(s):
        """test the RootTag model"""
        
        s.assertTrue(  isinstance(RootTag(), TagBase)  )
        root_tag = RootTag()
        s.assertEqual(root_tag.tag, "")
        s.assertEqual(root_tag.short_tag, "")
        s.assertEqual(root_tag.depth, 0)
        s.assertEqual(root_tag.parent.tag, "")
        s.assertEqual(root_tag.parent.short_tag, "")
        s.assertEqual(root_tag.parent.depth, 0)

    ####################################################################
    ## TEST CREATION
    def test_creation_low_level(s):
        """test low level creation of tags"""

        #s.assertEqual( Tag.get_if_exists('mytagbase'), None)
        tag = Tag.create_no_checks('mytagbase', None)
        s.assertTrue(tag != None)
        s.assertEqual(tag.tag, 'mytagbase')
        s.assertEqual(tag.short_tag, 'mytagbase')
        s.assertTrue(tag.id > 0)
        tag2 = Tag.get_if_exists('mytagbase')
        s.assertEqual(tag.tag, 'mytagbase')
        s.assertEqual(tag.short_tag, 'mytagbase')
        s.assertTrue(tag2 != None)
        s.assertEqual( tag.id, tag2.id )
        s.assertEqual( tag.depth, 1)
        

        tag_child = Tag.create_no_checks('mytagbase_child', tag)
        s.assertTrue(tag_child != None)
        s.assertEqual(tag_child.tag, 'mytagbase_child')
        s.assertEqual(tag_child.short_tag, 'mytagbase_child')
        s.assertTrue(tag_child.id > 0)
        s.assertEqual( tag_child.depth, 2)
        s.assertEqual( tag_child.parent.depth, 1)
        s.assertEqual( tag_child.parent.parent.depth, 0)
        s.assertEqual( tag_child.parent.parent.parent.depth, 0)
        s.assertEqual( tag_child.parent.id, tag.id )

        tag_id = tag.id
        tag_child_id = tag_child.id
        tag.delete()
        s.assertEqual( len(  Tag.objects.filter(id=tag_id)  ), 0 )
        s.assertEqual( len(  Tag.objects.filter(id=tag_child_id)  ), 0 )

        s.assertEqual( Tag.create_no_checks('').__class__, RootTag )
        s.assertEqual( Tag.get_if_exists('').__class__, RootTag )
        
        tag = Tag.create_no_checks('mytagbase2', None)
        with s.assertRaises(IntegrityError): 
            Tag.create_no_checks('mytagbase2', None)


    ####################################################################
    ## TEST CREATION
    def test_creation(s):
        """test creation of tags"""
        
        s.assertEqual( Tag.get_if_exists('mytag'), None)
        
        s.assertEqual( Tag.get_if_exists('mytag'), None)
        tag = Tag.get("mytag")
        s.assertTrue(tag != None)
        s.assertEqual(tag.tag, 'mytag')
        s.assertEqual(tag.short_tag, 'mytag')
        s.assertTrue( Tag.get_if_exists('mytag') != None)
        s.assertEqual(tag.parent.tag, "")
        s.assertEqual(tag.depth, 1)
        
        tag2 = Tag.get("mytag")
        s.assertEqual(tag.id, tag2.id)

        s.assertEqual(Tag.hierarchy_separator, '::')
        tag_child = Tag.get("mytag::child")
        s.assertTrue(tag_child != None)
        s.assertEqual(tag_child.tag, 'mytag::child')
        s.assertEqual(tag_child.short_tag, 'child')
        s.assertTrue( Tag.get_if_exists('mytag::child') != None)
        s.assertEqual(tag_child.depth, 2)
        s.assertEqual(tag_child.parent.tag, "mytag")

        tag3 = Tag.get(tag)
        s.assertEqual(tag3, tag)

    ####################################################################
    ## TEST CREATION
    def test_equality(s):
        """some specific equality tests"""
        
        # test whether if the underlying records are the same, then the objects are the same (__eq__)
        s.assertEqual( Tag.get('equal_tag'), Tag.get('equal_tag'))
        s.assertEqual( hash(Tag.get('equal_tag')), hash('equal_tag')  )
        s.assertEqual( hash(Tag.get('equal_tag')), hash(Tag.get('equal_tag'))  )
        
        # test whether equality works with unsaved object
        s.assertEqual( Tag.get('equal_tag'), Tag(_tag = 'equal_tag'))
        s.assertEqual( hash(Tag(_tag = 'equal_tag')), hash('equal_tag')  )
        s.assertEqual( hash(Tag(_tag = 'equal_tag')), hash(Tag(_tag = 'equal_tag'))  )

        # test whether sets work
        set1 = { Tag.get('equal_tag1'), Tag.get('equal_tag2'), Tag(_tag='equal_tag3') }
        set2 = { Tag.get('equal_tag2'), Tag.get('equal_tag1'), Tag(_tag='equal_tag3')  }
        s.assertEqual( set1, set2 )
         
    ####################################################################
    ## TEST HIERARCHY
    def test_hierarchy(s):
        """test hierarchy creation of tags"""

        s.assertTrue( Tag.get('aaa') != None)
        s.assertTrue( Tag.get('aaa::b') != None)
        s.assertTrue( Tag.get('aaa::bb') != None)
        s.assertTrue( Tag.get('aaa::bbb') != None)
        s.assertTrue( Tag.get('aaa::bbb::cc') != None)
        s.assertTrue( Tag.get('aaa::bbb::ccc') != None)

        
        s.assertTrue( Tag.get_if_exists('aaa') != None)
        s.assertTrue( Tag.get_if_exists('aaa::bbb') != None)
        s.assertTrue( Tag.get_if_exists('aaa::bbb::ccc') != None)
    
        aaa = Tag.get("aaa")
        s.assertEqual( aaa.depth, 1)
        s.assertEqual( aaa.parent.tag, "")
        s.assertEqual( aaa.direct_children, {Tag.get('aaa::b'), Tag.get('aaa::bb'), Tag.get('aaa::bbb')})
        s.assertEqual( aaa.children, {
            Tag.get('aaa::b'), 
            Tag.get('aaa::bb'), 
            Tag.get('aaa::bbb'), 
            Tag.get('aaa::bbb::cc'), 
            Tag.get('aaa::bbb::ccc')
        })
        s.assertEqual( aaa.family, {
            Tag.get('aaa'), 
            Tag.get('aaa::b'), 
            Tag.get('aaa::bb'), 
            Tag.get('aaa::bbb'), 
            Tag.get('aaa::bbb::cc'), 
            Tag.get('aaa::bbb::ccc')
        })
        
        aaa_bbb = Tag.get("aaa::bbb")
        s.assertEqual( aaa_bbb.depth, 2)
        s.assertEqual( aaa_bbb.parent.tag, "aaa")
        s.assertEqual( aaa_bbb.direct_children, {Tag.get('aaa::bbb::cc'), Tag.get('aaa::bbb::ccc')})
        s.assertEqual( aaa_bbb.children, {Tag.get('aaa::bbb::cc'), Tag.get('aaa::bbb::ccc')})

        aaa_bb = Tag.get("aaa::bb")
        s.assertEqual( aaa_bb.depth, 2)
        s.assertEqual( aaa_bb.parent.tag, "aaa")
        s.assertEqual( aaa_bb.direct_children, set())
        s.assertEqual( aaa_bb.children, set())

        aaa_bbb_ccc = Tag.get("aaa::bbb::ccc")
        s.assertEqual( aaa_bbb_ccc.depth, 3)
        s.assertEqual( aaa_bbb_ccc.parent.depth, 2)
        s.assertEqual( aaa_bbb_ccc.parent.parent.depth, 1)
        s.assertEqual( aaa_bbb_ccc.parent.parent.parent.depth, 0)
        s.assertEqual( aaa_bbb_ccc.direct_children, set())
        s.assertEqual( aaa_bbb_ccc.children, set())
        s.assertEqual( aaa_bbb_ccc.family, {aaa_bbb_ccc})
        

class TestTagging(TestCase):
    """
    testing the tagging
    """    
    def setUp(s):
        _Dummy(title='Record 1').save()
        _Dummy(title='Record 2').save()
        _Dummy(title='Record 3').save()
        _Dummy(title='Record 4').save()
        _Dummy(title='Record 5').save()
        _Dummy(title='Record 6').save()
        s.Data = _Dummy
        s.data = lambda x: s.Data.objects.get(id=x)

        s.tag = lambda x: Tag.get(x)
        
        
    def test_tagging(s):
        """tagging (using external tag access)"""
        
        d1 = s.data(1)
        d1.tag_add( s.tag('b1') )
        d1.tag_add( s.tag('b2') )
        d1.tag_add( s.tag('b3') )

        tags = d1.tags
        s.assertEqual( len(tags), 3)
        s.assertEqual( {t.tag for t in tags}, {'b1', 'b2', 'b3'})

        d1.tag_remove( s.tag('b2') )
        tags = d1.tags
        s.assertEqual( {t.tag for t in tags}, {'b1', 'b3'})

        d2 = s.data(2)
        d2.tag_add( s.tag('b1') )
        d2.tag_add( s.tag('b1') )
        d2.tag_add( s.tag('b2') )
        tags = d2.tags
        s.assertEqual( {t.tag for t in tags}, {'b1', 'b2'})

        d2.tag_remove( s.tag('b1') )
        tags = d2.tags
        s.assertEqual( {t.tag for t in tags}, {'b2'})

        d3 = s.data(3)
        d3.tag_add( s.tag('p1::c1') )
        d3.tag_add( s.tag('p1::c2') )
        tags = d3.tags
        s.assertEqual( {t.tag for t in tags}, {'p1::c1', 'p1::c2'})


    def test_tagging_str(s):
        """tagging (using internal tag access)"""

        d4 = s.data(4)
        d4.tag_add('b1')
        d4.tag_add('b2')
        d4.tag_add('b3')
        tags = d4.tags
        s.assertEqual( len(tags), 3)
        s.assertEqual( {t.tag for t in tags}, {'b1', 'b2', 'b3'})

        d4.tag_remove('b2')
        tags = d4.tags
        s.assertEqual( {t.tag for t in tags}, {'b1', 'b3'})


    def test_mixin_tag(s):
        """test tag method of the mixing structure"""
        
        d = s.data(5)
        s.assertEqual(d.tag('b1').tag, 'b1')
        s.assertEqual(d.tag('b1').depth, 1)
        s.assertEqual(d.tag('b1').short_tag, 'b1')

        s.assertEqual(d.tag('b1::c1').tag, 'b1::c1')
        s.assertEqual(d.tag('b1::c1').depth, 2)
        s.assertEqual(d.tag('b1::c1').short_tag, 'c1')

    def test_many_to_many_nh(s):
        """testing presentations tagged, and tags per presentation (flat tags)"""
        
        t1 = Tag.get('m2m_tag1')
        t2 = Tag.get('m2m_tag2')
        t3 = Tag.get('m2m_tag3')
        t4 = Tag.get('m2m_tag4')
        
        d1 = _Dummy(title='d1')
        d1.tag_add(t1)
        d1.tag_add(t2)
        d1.tag_add(t3)
        d1.save()
        s.assertEqual( len(d1.tags), 3)
        
        d2 = _Dummy(title='d2')
        d2.tag_add(t1)
        d2.save()
        s.assertEqual( len(d2.tags), 1)

        s.assertEqual( len(_Dummy.tagged_as(t1, False, False)), 2)
        s.assertEqual( len(_Dummy.tagged_as(t2, False, False)), 1)
        s.assertEqual( len(_Dummy.tagged_as(t3, False, False)), 1)

        s.assertEqual( set(_Dummy.tags_fromqs(_Dummy.objects.all())), {'m2m_tag1', 'm2m_tag2', 'm2m_tag3'} )

    def test_many_to_many_h(s):
        """testing presentations tagged, and tags per presentation (hierarchical tags)"""

        x = Tag.get('xxx')
        a = Tag.get('xxx::a')
        aa = Tag.get('xxx::a::a')
        ab = Tag.get('xxx::a::b')
        ac = Tag.get('xxx::a::c')
        b = Tag.get('xxx::b')
        ba = Tag.get('xxx::b::a')
        bb = Tag.get('xxx::b::b')

        d = _Dummy(title='dxxx')
        d.tag_add(x)
        
        da = _Dummy(title='da')
        da.tag_add(a)

        daa = _Dummy(title='daa')
        daa.tag_add(aa)

        #print(_Dummy.tagged_as(x, True))
        s.assertEqual( len(_Dummy.tagged_as(x, False, False)), 1)
        s.assertEqual( len(_Dummy.tagged_as(x, True, False)), 3)
        
        #print(_Dummy.tagged_as(a, True))
        s.assertEqual( len(_Dummy.tagged_as(a, False, False)), 1)
        s.assertEqual( len(_Dummy.tagged_as(a, True, False)), 2)
        
        #print(_Dummy.tagged_as(aa, True))
        s.assertEqual( len(_Dummy.tagged_as(aa, False, False)), 1)
        s.assertEqual( len(_Dummy.tagged_as(aa, True, False)), 1)


    def test_repr(s):
        """tests representation and TAG shortcut"""

        tag = RootTag()
        s.assertEqual( str(tag), "RootTag()")
        
        tag = TAG("")
        s.assertEqual( str(tag), "RootTag()")
        
        tag = TAG("single")
        s.assertEqual( str(tag), "TAG('single')")
        
        tag = TAG("aaa::bbb")
        s.assertEqual( str(tag), "TAG('aaa::bbb')")

        



        








 
