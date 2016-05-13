"""
a generic tag model for Django

Copyright (c) Stefan LOESCH, oditorium 2016. All rights reserved.
Licensed under the Mozilla Public License, v. 2.0 <https://mozilla.org/MPL/2.0/>
"""
__version__ = "1.4"
__version_dt__ = "2016-05-13"
__copyright__ = "Stefan LOESCH, oditorium 2016"
__license__ = "MPL v2.0"

from django.db import models
from django.core.signing import Signer, BadSignature
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

import json

#from itertools import chain


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
    def direct_children_g(self):
        """the direct children of the current tag (returns generator of objects, not tag strings)"""
        raise NotImplementedError()

    @property
    def is_leaf(self):
        """
        a tag is a leaf iff it has no children
        """
        return len(tuple(self.direct_children_g)) == 0

    @property
    def direct_children(self):
        """
        the direct children of the current tag (returns the objects, not the tag strings)
        """
        return { t for t in self.direct_children_g }

    @property
    def children(self):
        """
        the children of the current tag (returns the objects, not the tag strings)
        """
        children = self.direct_children
        for t in self.direct_children:
            children = children.union(t.children)
        return children

    @property
    def family(self):
        """
        the children plus the tag itself (returns set of objects, not the tag strings)
        """
        return self.children.union({self})

    @property
    def leaves(self):
        """
        all leaf-tags below self, as generator of objects
        """
        if self.is_leaf: return (self,)
        else: return ( t1 for t2 in self.direct_children_g for t1 in t2.leaves )
              #return tuple( t.leaves for t in self.direct_children_g )
    
    @classmethod
    def all_leaves(cls, root_tags=None):
        """
        generator for all leaves below root_tags (or cls.root_tags() if None)
        """
        if root_tags == None: root_tags = cls.root_tags()
        return ( t2 for t1 in root_tags for t2 in t1.leaves )
        
    @classmethod
    def root_tags(cls):
        """returns a generator of root tags (ie tags with no parent), ordered by id"""
        raise NotImplementedError()
    
    def delete(self, *args, **kwargs):
        """
        delete that tag (and all below it)
        """
        try: super().delete(*args, **kwargs)
        except: raise NotImplementedError()

    @classmethod
    def parent_tagstr(cls, tagstr):
        """
        the tag string of the parent tag
        """
        try: return tagstr.rsplit(cls.hierarchy_separator, 1)[-2]
        except IndexError: return None

    @property
    def short_tag(self):
        """
        the stub tag string of the child tag
        """
        return self.tag.rsplit(self.hierarchy_separator, 1)[-1]
        
    @classmethod
    def get(cls, tagstr):
        """
        gets the tag object corresponding to the tag string (possibly creating it and entire hierarchy)
        """
        
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
        """
        deletes the tag object corresponding to the tag string (possibly deleting the entire hierarchy below)
        """
        tag = cls.get(tagstr)
        if tag != None: tag.delete()
        
    @classmethod
    def get_if_exists(cls, tagstr):
        """
        gets the tag object corresponding to the tag string if it exists, None else
        """
        raise NotImplementedError() 
        
    @classmethod
    def create_no_checks(cls, tagstr, parent_tag=None):
        """creates the tag object corresponding to the tag string (must not previously exist, exception else)"""
        raise NotImplementedError()
        
    @property   
    def depth(self):
        """
        returns the depth of the current tag in the hierachy (root=0)
        """
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
        
    _parent_tag = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
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
        if not self._parent_tag: return RootTag()
        return self._parent_tag

    @property
    def direct_children_g(self):
        """
        the direct children of the current tag (returns generator of objects, not tag strings)
        """
        return ( t for t in self.__class__.objects.filter(_parent_tag=self) )

    @classmethod
    def root_tags(cls):
        """
        returns a generator of root tags (ie tags with no parent), ordered by id
        """
        return (t for t in cls.objects.filter(_parent_tag=None).order_by('id'))

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

#############################################################
## ERROR / SUCCESS
def _error(msg, status=None):
    if status == None: status = 404
    return JsonResponse({'success': False, 'errmsg': msg}, status=status)

def _success(data, status=None):
    if status == None: status = 200
    return JsonResponse({'data': data, 'success': True}, status=status)

#############################################################
## EXCEPTIONS
class TokenSignatureError(RuntimeError): pass       # the token signature is invalid
class TokenFormatError(RuntimeError): pass          # the token format is invalid
class IllegalCommandError(RuntimeError): pass       # that command is not valid
class ItemDoesNotExistError(RuntimeError): pass     # the item does not exist
class TagDoesNotExistError(RuntimeError): pass      # the tag does not exist
class TokenContentError(RuntimeError): pass         # the token content is invalid
class TokenDefinitionError(RuntimeError): pass      # bad parameters when defining a token


#############################################################
## TOKEN
class Token():
    """
    allows definition tokens for the tag API
    """
    def __init__(s, token):
        try: token = Signer(sep=s.separators, salt=s.salt).unsign(token)
        except BadSignature: raise TokenSignatureError(token)
        s.token = token.split(s.separator)
        if len(s.token) != 4: raise TokenFormatError("Invalid token format [1]")
    
    separators=":::"
    separator="::"
    separator2=":"
    salt="token"
    
    @classmethod
    def create(cls, namespace, command, tag_id=None, item_id=None):
        """
        create a token
        
        PARAMETERS
        - namespace: the token namespace (string, minimum 2 characters)
        - command: the token command (can be a string, or a list of strings if it uses parameters)
        - tag_id: the tag id (if any) this command relates to
        - item_id: the item id (if any) this command relates to
        """
        if len(namespace) < 2: raise TokenDefinitionError("namespace minimum 2 characters")
        if not isinstance(command, str): command = cls.separator2.join(command)
        token = cls.separator.join([namespace, command, str(tag_id), str(item_id)])
        return Signer(sep=cls.separators, salt=cls.salt).sign(token)

    @property
    def namespace(s):
        """
        the token namespace
        """
        return s.token[0]
        
    @property
    def command(s):
        """
        the token command (without paramters)
        """
        return s.token[1].split(s.separator2)[0]
        
    @property
    def parameters(s):
        """
        the token command parameters (as list)
        """
        return s.token[1].split(s.separator2)[1:]
        
    @property
    def numparameters(s):
        """
        the number of token parameters
        """ 
        return len(s.parameters)

    @property
    def tag_id(s):
        """
        the (numeric) tag id, or None
        """ 
        value = s.token[2]
        if value == "None": return None
        return int(value)
        
    @property
    def item_id(s):
        """
        the (numeric) item id, or None
        """ 
        value = s.token[3]
        if value == "None": return None
        return int(value)

    def __str__(s):
        return "Token({})"




#############################################################
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

    _tag_references = models.ManyToManyField(Tag, blank=True)
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

    def tag_toggle(self, tag_or_tagstr):
        """
        toggles a tag on a specific record
        """
        raise NotImplementedError('tag_toggle')

    @property
    def tags(self):
        """
        returns all tags from that specific record (as set)
        """
        return {t for t in self.tags_qs}

    @property
    def tags_str(self):
        """
        returns all tags from that specific record (as string)
        """
        return " ".join([t.tag for t in self.tags_qs])

    @property
    def tags_qs(self):
        """
        returns all tags from that specific record (as queryset)
        """
        return self._tag_references.all()
    
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

    ########################################
    ## TAG TOKEN XXX
    @classmethod
    def tag_token(cls, command, tag_or_tag_id=None, item_or_item_id=None):
        """
        generic token generation

        command: one of 'add', 'remove', 'toggle'
        tag_id,item_id: identifying the tag and item respectively
        """
        if not command in ['add', 'remove', 'toggle']: raise IllegalCommandError(command)
        if not isinstance(item_or_item_id, int): item_or_item_id = item_or_item_id.id
        if not isinstance(tag_or_tag_id, int): tag_or_tag_id = tag_or_tag_id.id
        return Token.create(cls.__name__, command, tag_or_tag_id, item_or_item_id)

    def tag_token_add(s, tag_or_tag_id):
        """
        creates a token to allow adding a tag
        """
        return s.tag_token("add", tag_or_tag_id, s.id)

    def tag_token_remove(s, tag_or_tag_id):
        """
        creates a token to allow adding a tag
        """
        return s.tag_token("remove", tag_or_tag_id, s.id)

    def tag_token_toggle(s, tag_or_tag_id):
        """
        creates a token to allow adding a tag
        """
        return s.tag_token("toggle", tag_or_tag_id, s.id)

    def tag_token_all(s, tag_or_tag_id):
        """
        return a dict of all tokens for this tag, item
        """
        return {
            'tag':      tag_or_tag_id,
            'add':      s.tag_token_add(tag_or_tag_id),
            'remove':   s.tag_token_remove(tag_or_tag_id),
            'toggle':   s.tag_token_toggle(tag_or_tag_id),
        }

    @property
    def tags_token_all(s):
        """
        returns a list of dicts for all tags, and all tokens for each of those tags, for this item
        
        NOTES
        - all tags being defined as all Tag.all_leaves
        - the dicts are those created by `tag_token_all`
        """
        return [ s.tag_token_all(t) for t in Tag.all_leaves()]
        

    ########################################
    ## TAG TOKEN EXECUTE
    @classmethod
    def tag_token_execute(cls, token, params=None):
        """
        execute a token command

        NOTES
        - `token` is the relevant token
        - `params` are the parameters 
        ##(can be bytes; if string assumes it is json encoded)
        """
        t = Token(token)
        if t.namespace != cls.__name__: 
            raise TokenContentError("using {} token for a {} object".format(t.namespace, cls.__name__))
        #if isinstance(params, bytes): params = params.decode()
        #if isinstance(params, str): 
        #    try: params = json.loads(params)
        #    except: raise ParamsError(params) 

        
        

        try: item = cls.objects.get(id=t.item_id)
        except: raise ItemDoesNotExistError(t.item_id)
        
        try: tag = Tag.objects.get(id=t.tag_id)
        except: raise TagDoesNotExistError(t.tag_id)
        
        # add/remove/toggle
        if    t.command == "add":     item.tag_add(tag)
        elif  t.command == "remove":  item.tag_remove(tag)
        elif  t.command == "toggle":  item.tag_toggle(tag)

        # error
        else:
            raise IllegalCommandError(t.command)



    ########################################
    ## TAG AS VIEW
    @classmethod
    def tag_as_view(cls):
        """
        returns a API view function that can be used directly in an `urls.py` file

        NOTE:
        - the view function expects POST for all requests, even those that are only reading data
        - the data has to be transmitted in json, not URL encoded
        - the response is json; fields are a `success` field (true or false), and an `errmsg` 
            field in case of non success

        PARAMETERS:
        - token: the API token thatdetermines the request


        USAGE
        In the `urls.py` file:

            urlpatterns += [
                url(r'^api/somemodel$', SomeModel.tag_as_view(), name="api_somemodel_tag"),
            ]

        In the `models.py` file:

            class SomeModel(TagMixin, models.Model):
                ...

        In the `views.py` file:
            context['item'] = SomeModel.objects.get(id=...)
            ...

        In the `template.html` file:

            <ul class='taglist'>
            {% for t in item.tags_token_all %}
            <li>
            {{t.tag.tag}}
            <span class='active active-tag active-tag-add' data-tag-token='{{t.add}}'>add</span>    
            <span class='active active-tag active-tag-remove' data-tag-token='{{t.remove}}'>remove</span>   
            </li>
            {% endfor %}
            </ul>
            
            <script>
            $('.active-tag').on('click', function(e){
                var target = $(e.target)
                var token = target.data('tag-token')
                var data = JSON.stringify({token: token, params: {}})
                $.post("{% url 'api_somemodel_tag'%}", data).done(function(){...})
            })
            </script>


        """
        @csrf_exempt
        def view(request):
    
            if request.method != "POST": return _error("request must be POST")
            
            try: data = json.loads(request.body.decode())
            except: 
                raise
                return _error('could not json-decode request body [{}]'.format(request.body.decode()))

            try: token = data['token']
            except: return _error('missing token')

            params = data['params'] if 'params' in data else None

            try: result = cls.tag_token_execute(token, params)
            except TokenSignatureError as e: return _error('token signature error [{}]'.format(str(e)))
            except TokenFormatError as e: return _error('token format error [{}]'.format(str(e)))
            #except ParamsError as e: return _error('parameter error [{}]'.format(str(e)))
            except ItemDoesNotExistError as e: return _error('item does not exist [{}]'.format(str(e)))
            except TagDoesNotExistError as e: return _error('tag does not exist [{}]'.format(str(e)))
            except Exception as e: return _error('error executing token [{}::{}]'.format(type(e), str(e)))

            return _success(result)

        return view
    

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


# THIS CODE SHOULD BE CONVERTED INTO UNIT TESTS
# TODO
# 
# from issuetracker.models import Tag
# from issuetracker.models.tag import Token
# Token.create('myns', 'mycmd')
# s=Token.create('myns', 'mycmd',1,100)
# s
# t=Token(s)
# t.namespace
# t.command
# t.tag_id
# t.item_id
# 
# s='myns::mycmd::1::100:::b9A_IT7PYroZXeBld1s0mqliyZY'
# t=Token(s)
# 
# 
# from issuetracker.models import Issue
# 
# Issue.tag_token("add", 1, 100)
# Issue.tag_token("remove", 1, 100)
# Issue.tag_token("toggle", 1, 100)
# 
# i=Issue.objects.all()[0]
# i.tag_token_add(123)
# i.tag_token_remove(123)
# i.tag_token_toggle(123)
# 
# from issuetracker.models import Issue
# from issuetracker.models import Tag
# i=Issue.objects.all()[0]
# s = i.tag_token_add(123)
# s
# Issue.tag_token_execute(s)
# 
# tag = Tag.objects.all()[0]
# tag
# s = i.tag_token_add(tag)
# s
# i.tags
# s = i.tag_token_add(tag)
# Issue.tag_token_execute(s)
# i.tags
# s = i.tag_token_remove(tag)
# Issue.tag_token_execute(s)
# i.tags
# s = i.tag_token_toggle(tag)
# Issue.tag_token_execute(s)
# i.tags
# 
# i.tag_token_all(tag)
# 
# i.tags_token_all



        

    
    
   
    

