"""
a generic tag model for Django

Copyright (c) Stefan LOESCH, oditorium 2016. All Rights Reserved.
Licensed under the MIT License <https://opensource.org/licenses/MIT>.
"""
__version__ = "1.2+"
__version_dt__ = "2016-04-08"
__copyright__ = "Stefan LOESCH, oditorium 2016"
__license__ = "MIT"

from django.db import models

#####################################################################################################
## TAG BASE
class TagBase(object):
    """
    base class for a hierarchical tag object
    """
    @property
    def tag(self):
        """the actual tag string, including (in case of a hierarchical tag) the hierarchy separators"""
        raise NotImplementedError()
        
    @property
    def parent(self):
        """the parent of the current tag (returns the object, not the tag )"""
        raise NotImplementedError()

    @property
    def children(self):
        """the children of the current tag (returns the objects, not the tag strings)"""
        raise NotImplementedError()

    @property
    def direct_children(self):
        """the children of the current tag (returns the objects, not the tag strings)"""
        raise NotImplementedError()

    @property
    def family(self):
        """the children plus the tag itself (returns the objects, not the tag strings)"""
        return self.children.union({self})

    def delete(self, *args, **kwargs):
        """delete that tag (and all below it)"""
        try: super().delete(*args, **kwargs)
        except: raise NotImplementedError()

    @classmethod
    def parent_tagstr(cls, tagstr):
        """the tag string of the parent tag"""
        try: return tagstr.rsplit(cls.hierarchy_separator, 1)[-2]
        except IndexError: return None

    @property
    def short_tag(self):
        """the stub tag string of the child tag"""
        return self.tag.rsplit(self.hierarchy_separator, 1)[-1]
        
    @classmethod
    def get(cls, tagstr):
        """gets the tag object corresponding to the tag string (possibly creating it and entire hierarchy)"""
        
        if tagstr==None: return None
            # play nicely with None tagstrings (they just result in a None tag)
        
        if isinstance(tagstr, TagBase): return tagstr
            # play nicely with tag strings already converted into tags
            
        tag = cls.get_if_exists(tagstr)
        if tag: return tag
            # get_if_exists returns the tag corresponding to the tag string iff it exists, None else
            # so if we get an object back, this is the tag object and we return it
        
        parent_tagstr = cls.parent_tagstr(tagstr)
        parent_tag = cls.get(parent_tagstr)
            # parent_tagstr is the string representation of the parent tag
            # we recursively call get to retrieve (and create, if need be!) that tag
            # in case this is a top-level tag, parent_tagstr() returns None, and get() then also returns None

        tag = cls.create_no_checks(tagstr, parent_tag)
            # this creates new tag with string representation tagstr, and parent object parent_tag
            # in case this is a top-level tag, parent_tag will be None

        return tag
    
    @classmethod 
    def deltag(cls, tagstr):
        """deletes the tag object corresponding to the tag string (possibly deleting the entire hierarchy below)"""
        tag = cls.get(tagstr)
        if tag != None: tag.delete()
        
    @classmethod
    def get_if_exists(cls, tagstr):
        """gets the tag object corresponding to the tag string if it exists, None else"""
        raise NotImplementedError() 
        
    @classmethod
    def create_no_checks(cls, tagstr, parent_tag=None):
        """creates the tag object corresponding to the tag string (must not previously exist, exception else)"""
        raise NotImplementedError()
        
    @property   
    def depth(self):
        """returns the depth of the current tag in the hierachy (root=0)"""
        parent = self.parent
        if  parent != None: return 1 + parent.depth
        return 1
        
    hierarchy_separator = "::"
        # defines the string that separtes tags in the hierarchy; for example:
        # assume hierarchy_separator == '::', then a::b::c is subtag of a::b is subtag of a

    def __repr__(s):
        return "{1}.get('{0.tag}')".format(s, s.__class__.__name__)

    def __str__(s):
        return s.__repr__()

    
#####################################################################################################
## ROOT BASE
class RootTag(TagBase):
    """
    the topmost tag of any hierarchy
    """
    
    @property
    def tag(self):
        return ""
        
    @property
    def parent(self):
        return self
        
    @property
    def depth(self):
        return 0 

    @classmethod
    def get(cls, tagstr):
        if tagstr != "" and tagstr != None: raise NotImplementedError()
        return cls()

    def __repr__(s):
        return "RootTag()"
   
        



#####################################################################################################
## TAG      
class Tag(TagBase, models.Model):
    """
    the actual class implementing tags
    
    USAGE
    
        Tag.hierarchy_separator = '::'
        
        tag = Tag.get('aaa')
        print (tag.tag)                     # 'aaa'
        print (tag.short_tag)               # 'aaa'
        print (tag.depth)                   # 1
        print (tag.parent.tag)              # ''
        print (tag.parent.depth)            # 0
        
        tag = Tag.get('aaa::bbb')
        print (tag.tag)                     # 'aaa::bbb'
        print (tag.short_tag)               # 'bbb'
        print (tag.depth)                   # 2
        print (tag.parent.tag)              # 'aaa'
        print (tag.parent.depth)            # 1
        
    """
    
    _tag = models.CharField(max_length=255, unique=True, blank=True, default="", null=False, db_index=True)
        # that's the actual tag, including (in case of a hierarchical tag) the tag separator
        
    _parent_tag = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
        # the parent of the current tag, if any

    def __eq__(self, other):
        if isinstance(other, self.__class__): 
            return self._tag == other._tag
                # if we do it on the ids it does not work for not-yet-saved tags!
        else: return False

    def __hash__(self):
        return str(self._tag).__hash__()
        
    @property
    def tag(self):
        """the actual tag string, including (in case of a hierarchical tag) the hierarchy separators"""
        return self._tag
        
    @property
    def parent(self):
        """
        the parent of the current tag (returns the object, not the tag string)
        """
        parent = self._parent_tag
        if parent == None: return RootTag()
        return parent

    @property
    def direct_children(self):
        """
        the direct children of the current tag (returns the objects, not the tag strings)
        """
        return { t for t in self.__class__.objects.filter(_parent_tag=self)}

    @property
    def children(self):
        """
        the children of the current tag (returns the objects, not the tag strings)
        """
        children = self.direct_children
        for t in self.direct_children:
            children = children.union(t.children)
        return children


    @classmethod
    def get_if_exists(cls, tagstr):
        """
        gets the tag object corresponding to the tag string if it exists, None else
        """
        if tagstr=="": return RootTag()
        try: return cls.objects.get(_tag=tagstr)
        except: return None

    @classmethod
    def create_no_checks(cls, tagstr, parent_tag=None):
        """
        creates the tag object corresponding to the tag string (must not previously exist, exception else)
        """
        if tagstr=="": return RootTag()
        newtag = cls(_tag=tagstr, _parent_tag=parent_tag)
        newtag.save()
        return newtag

    def __repr__(s):
        return "TAG('{0.tag}')".format(s, s.__class__.__name__)
    

def TAG(tagstr):
    """convenience method for Tag.get"""
    return Tag.get(tagstr)
    
    
#####################################################################################################
## TAG MIXIN
class TagMixin(models.Model):
    """
    a mixin for Django models, linking them to the Tag model

    NOTES
    - this mixin contains a model field (`_tag_references`); in order for this field to actually
        appear in the database table of the final the mixin must derive from `models.Model`*
        
    - for this table to not appear in the database, we need the Meta class with `abstract=True`

    USAGE
    Basic usage is here. See the tests for more detailed examples.
    
        class MyTaggedClass(TagMixin, models.Model):
            ...
            
        tc = MyTaggedClass()
        tc.tag_add('mytag1')
        tc.tag_add('mytag1')
        tc.tags                                 # {TAG('mytag1'), TAG('mytag2')}
        tc.tag_remove('mytag1')
        tc.tags                                 # {TAG('mytag2')}
        MyTaggedClass.tagged_as('mytag2')       # set(tc)
    
    *see <http://stackoverflow.com/questions/6014282/django-creating-a-mixin-for-reusable-model-fields>
    """

    _tag_references = models.ManyToManyField(Tag)
        # that's the key connection to the tags field

    class Meta:
        abstract = True

    save_if_necessary = True
        # if True, tag_add will save the record if it needs to in order to establish the relationship
        # otherwise tag_add proceeds, and an exception is thrown


    @staticmethod
    def tag(tagstr):
        return Tag.get(tagstr)

    def tag_add(self, tag_or_tagstr):
        """
        adds a tag to a specific record
        """
        if self.id == None:
            if self.save_if_necessary: self.save()
        self._tag_references.add( Tag.get(tag_or_tagstr) )

    def tag_remove(self, tag_or_tagstr):
        """
        removes a tag from a specific record
        """
        self._tag_references.remove( Tag.get(tag_or_tagstr) )

    @property
    def tags(self):
        """
        returns all tags from that specific record (as set)
        """
        return {t for t in self._tag_references.all()}

    @property
    def tags_str(self):
        """
        returns all tags from that specific record (as string)
        """
        return " ".join([t.tag for t in self._tag_references.all()])
    
    @classmethod
    def tags_fromqs(cls, self_queryset, as_queryset=False):
        """
        returns all tags that are in relation to self_queryset (return tags as flat list or queryset)

        USAGE
            qs = MyTaggedClass.objects.filter(...)
            tags = MyTaggedClass.tags_fromqs(qs)                            # ['tag1', 'tag2', ...]
            tags_qs = MyTaggedClass.tags_fromqs(qs, as_queryset=True )      # queryset
        """
        # http://stackoverflow.com/questions/4823601/get-all-related-many-to-many-objects-from-a-django-queryset
        kwargs = {(cls.__name__+"__in").lower(): self_queryset}
        tag_queryset = Tag.objects.filter(**kwargs).distinct()
        if as_queryset: return tag_queryset
        return [tag for tag in tag_queryset.values_list('_tag', flat=True)]    

    @classmethod
    def tagged_as(cls, tag_or_tagstr, include_children=True, as_queryset=True):
        """
        returns all records that are tagged with this tag (and possibly its children)
        
        NOTES
        - if `include_children` is true'ish, all records tagged with this tag or its children
            are returned, otherwise only with this tag
        - if `as_queryset` is true'ish, a queryset is returned that can be acted upon further
            (eg by filtering); otherwise a set is returned
        """
        tag = Tag.get(tag_or_tagstr)
        if include_children: tag = tag.family
        else: tag = [tag]
        qset = cls.objects.filter(_tag_references__in=tag)
        if as_queryset: return qset
        return {record for record in qset}

        # attr = cls.__name__.lower()+"_set"
        # items = {i for i in getattr(tag, attr).all()}
        #     # eg tag._dummy_set.all()
        # if not include_children: return items
        # for ctag in tag.children:
        #     items = items.union( cls.tagged_as(ctag, include_children=True) )
        # return items
    

#####################################################################################################
## _DUMMY      
class _Dummy(TagMixin, models.Model):
    """
    a dummy model allowing to test tagging
    """

    title = models.CharField(max_length=32, unique=True, blank=True, default="", null=False, db_index=True)
        # some text that allows to identify the record

    def __repr__(self):
        return "{1}(title='{0.title}')".format(self, self.__class__.__name__)


        

    
    
   
    

