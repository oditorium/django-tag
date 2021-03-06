# django-tag
_A Tagging App for Django_

## Installation
### Installing the `tag` app

The `tag` app can simply be copied into an existing Django project (tested with Python 3.5/ Django 1.9).
After it has been connected in the settings file it should work. To run the tests, run the following
commands from the project directory

    python3 manage.py makemigrations
    python3 manage.py migrate
    python3 manage.py test tag

### Heroku installation

After installing the Heroku [Toolbelt](https://toolbelt.heroku.com/) run the following commands:

    git clone https://github.com/oditorium/django-slack.git
    cd django-slack
    heroku create
    heroku config:set HEROKU=1
    git push heroku +master


## Using the `tag` app 

The `tag` library defines the following classes within the `models` package (`models.tag` to be precise,
but it is imported into the package namespace). The main classes defined are:

- `Tag`: the main class defining hierarchical tags

- `TagMixin`: a mixing for model classes that allows them to become tagged

It also defines the following classes which are not usually needed when using the tag library

- `TagBase`: an abstract base class defining the tag interface

- `RootTag`: a trivial tag space without any tags, serving as the root space for all
    hierarchical tags
    
- `_Dummy`: an example model using the `TagMixin` to create tagged items; required to run
    the unit tests
    
## Using `Tag`s

The `Tag` model creates a hierarchical tag structure where *parent* tags can spawn multiple *child* tags,
who in turn can become parent tags for the next generation of children. Tags are created and retrieved
using the class method `get`
    
    parent = Tag.get('parent')
    child1 = Tag.get('parent::child1')
    child2 = Tag.get('parent::child2')
    gchild = Tag.get('parent::child2::grandchild')

where the `::` is used as separator (this choice can be changed by adjusting the `hierarchy_separator` c
lass property). There are a number of methods that allow to read tag data

    gchild.tag                  # 'parent::child2::grandchild'
    gchild.short_tag            # 'grandchild'
    
For traversing the hierarchy we have the following methods

    parent.children             # {child1, child2, gchild}
    parent.direct_children      # {child1, child2}
    parent.family               # {parent, child1, child2}
    child1.parent               # parent
    parent.depth                # 1
    child1.depth                # 2
        
and finally, tags can be deleted as follows:

    Tag.deltag('parent::child2::grandchild')        # deletion using class method
    child2.delete()                                 # deletion using instance method

Note that deleting a parent tag deletes all children (except for the root tag) 


## Using `TagMixin`

### In Django

The `TagMixin` class allows to tag record of Django models with `Tag` class defined above, being mindful
of the hierarchy of those tags (ie, a record tagged `aaa:bbb` will be considered being tagged `aaa` as well
as `aaa:bbb`). Under the hood this works using a many-to-many field called `_tag_references`, but this
detail has been abstracted away. For example, if we define `MyTaggedClass` as follows (note the multiple 
inheritance!)

    class MyTaggedClass(TagMixin, models.Model):
        title = CharField(...)

then this automatically makes `MyTaggedClass` tagged. This means the following properties and methods are
available to manipulate tagging

    rec1 = MyTaggedClass(title='Rec1')
    rec2 = MyTaggedClass(title='Rec2')
    rec1.tag_add('tag1')
    rec1.tag_add('aaa:111')
    rec2.tag_add('aaa:222')
    rec1.tags                                                   # {aaa:111, tag1}
    rec2.tags                                                   # {aaa:222}
    MyTaggedClass.tagged_as('aaa:111', as_queryset=False)       # {rec1}
    MyTaggedClass.tagged_as('aaa', as_queryset=False)           # {rec1, rec2}
    MyTaggedClass.tagged_as('aaa', include_children=False)      # -empty queryset-
    qs = MyTaggedClass.objects.all()
    MyTaggedClass.tags_fromqs(qs)                               # ['aaa:111', 'aaa:222']
    rec1.tag_remove('tag1')
    rec1.tags                                                   # {aaa:111}


### Via the API

This model class can then also be directly connected to a view that allows changing those tags 

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

    <ul class='taglist'>
        {% for t in item.tags_token_all %}
        <li>
            {{t.tag.tag}}
            <span class='active-tag' data-token='{{t.add}}' data-msg='added tag {{t.tag.tag}}'>add</span>    
        </li>
        {% endfor %}
    </ul>
    
    <script>
    $('.active-tag').on('click', function(e){
        var target = $(e.target)
        var token = target.data('token')
        var msg = target.data('msg')
        var data = JSON.stringify({token: token, params: {}, reference: {msg: msg}})
        $.post("{% url 'api_somemodel_tag'%}", data).done(function(r){console.log(r.reference.msg)})
    })
    </script>


## Contributions

Contributions welcome. Send us a pull request!


## Change Log
The idea is to use [semantic versioning](http://semver.org/), even though initially we might make some minor
API changes without bumping the major version number. Be warned!

- **v1.5** added `has_tag`, and returning more data when the API is called

- **v1.4** added `tag_as_view` as well as the related token generation and execution functions

- **v1.3** some restructuring; added a number of new properties and methods (eg `leaves`, `root_tags, ...); now preferring generators over lists/tuples; `changed license to MPL v2.0; bugfix: allow empty tags and empty parents of tags

- **v1.2** added `tags_fromqs` and associated tests

- **v1.1** added `family` property for tags and cleaned up `TagBase` and `RootTag`; added `tags_str` property
to `TagMixin` and modified `tagged_as` to use filters and to alternatively return a query set

- **v1.0** Initial Release
