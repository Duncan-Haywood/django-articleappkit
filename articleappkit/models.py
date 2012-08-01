import datetime

from django.db import models
from django.core.files.images import get_image_dimensions
from django.utils.translation import ugettext_lazy as _

#
#  Can we use a factory function that takes a configuration, updates the default
#  configuration and returns the class? The result would be like
#
#  ArticleBase = get_articlebase(CONFIG)
#
#  class MyArticle(ArticleBase)
#

from articleappkit.fields import ModelUploadFileField


def get_articlebase(custom_config=None):

    from articleappkit.settings import USER_SETTINGS as config

    if custom_config is not None:
        config.update(custom_config)

    class ArticleBase(models.Model):
        """
        Base article content
        """
        title = models.CharField(
            _(config['FIELDNAMES'].get('title', 'title')),
            max_length=255)
        subtitle = models.CharField(
            _(config['FIELDNAMES'].get('subtitle', 'subtitle')),
            max_length=255,
            blank=True,
            null=True)
        slug = models.SlugField(
            _(config['FIELDNAMES'].get('slug', 'slug')),
            max_length=255)
        summary = models.TextField(
            _(config['FIELDNAMES'].get('summary', 'summary')),
            blank=True,
            null=True)
        content = models.TextField(_(config['FIELDNAMES'].get('content', 'content')))

        create_date = models.DateTimeField(
            _(config['FIELDNAMES'].get('create_date', 'create_date')),
            blank=True,
            editable=False)
        update_date = models.DateTimeField(
            _(config['FIELDNAMES'].get('update_date', 'update date')),
            help_text=_("The update date/time to display to the user"),
            blank=True,
            null=True)
        modified_date = models.DateTimeField(
            _(config['FIELDNAMES'].get('modified_date', 'modified date')),
            default=datetime.datetime.now,
            blank=True,
            editable=False)

        class Meta:
            abstract = True
            get_latest_by = 'modified_date'
            ordering = ('-modified_date',)

            if config['UNIQUE_TOGETHER']:
                unique_together = config['UNIQUE_TOGETHER']

        def __unicode__(self):
            return self.title

        def save(self, *args, **kwargs):
            if not self.id:
                self.create_date = datetime.datetime.now()
            super(ArticleBase, self).save(*args, **kwargs)

        objects = models.Manager()

    return ArticleBase

###
# Attribution Mixins
###


def get_singleauthormixin(custom_config=None):

    from articleappkit.settings import USER_SETTINGS as config

    if custom_config is not None:
        config.update(custom_config)

    class SingleAuthorMixin(models.Model):
        """
        A mixin that adds a relation to another model (typically auth.User)
        """
        author = models.ForeignKey(
            config['AUTHOR_MODEL'],
            verbose_name=_(config['FIELDNAMES'].get('author', 'author')),
            blank=True,
            null=True,
            limit_choices_to=config['AUTHOR_MODEL_LIMIT'])

        class Meta:
            abstract = True
    return SingleAuthorMixin


def get_multiauthormixin(custom_config=None):

    from articleappkit.settings import USER_SETTINGS as config

    if custom_config is not None:
        config.update(custom_config)

    class MultiAuthorMixin(models.Model):
        """
        A mixin that adds a many-to-many relation to another model
        """
        authors = models.ManyToManyField(
            config['AUTHOR_MODEL'],
            verbose_name=_(config['FIELDNAMES'].get('authors', 'authors')),
            blank=True,
            null=True,
            limit_choices_to=config['AUTHOR_MODEL_LIMIT'])

        class Meta:
            abstract = True
    return MultiAuthorMixin


def get_nonstaffauthormixin(custom_config=None):

    from articleappkit.settings import USER_SETTINGS as config

    if custom_config is not None:
        config.update(custom_config)

    class NonStaffAuthorMixin(models.Model):
        """
        A mixin that adds a character field to set a one-time or non-staff author
        """
        non_staff_author = models.CharField(
            _(config['FIELDNAMES'].get('non_staff_author', 'non-staff author')),
            max_length=200,
            blank=True,
            null=True,
            help_text=_("An HTML-formatted rendering of an author(s) not on staff."))

        class Meta:
            abstract = True
    return NonStaffAuthorMixin


###
# Key Image Mixin
###

def get_keyimagemixin(custom_config=None):

    from articleappkit.settings import USER_SETTINGS as config

    if custom_config is not None:
        config.update(custom_config)

    class KeyImageMixin(models.Model):
        """
        A mixin that adds a key image field and attribution
        """
        key_image = ModelUploadFileField(
            _(config['FIELDNAMES'].get('key_image', 'key image')),
            null=True,
            blank=True,
            storage=config['IMAGE_STORAGE'](),
            upload_to=config['IMAGE_UPLOAD_TO'])
        key_image_width = models.IntegerField(editable=False, blank=True, null=True)
        key_image_height = models.IntegerField(editable=False, blank=True, null=True)
        key_image_credit = models.CharField(
            _(config['FIELDNAMES'].get('key_image_credit', 'key image credit')),
            max_length=255,
            blank=True,
            null=True)

        class Meta:
            abstract = True

        def save(self, *args, **kwargs):
            if self.key_image:
                width, height = get_image_dimensions(self.key_image.file, close=True)
            else:
                width, height = None, None

            self.key_image_width = width
            self.key_image_height = height

            super(KeyImageMixin, self).save(*args, **kwargs)
    return KeyImageMixin


###
# PublishingMixin
###

def get_pubworkflowmixin(custom_config=None):

    from articleappkit.settings import USER_SETTINGS as config

    if custom_config is not None:
        config.update(custom_config)

    class PubWorkflowManager(models.Manager):
        def published(self):
            qset = super(PubWorkflowManager, self).get_query_set()
            qset.filter(
                status=config['PUBLISHED_STATUS'],
                pub_date__lte=datetime.datetime.now(),
                pub_time__lte=datetime.datetime.now())
            return qset

    class PubWorkflowMixin(models.Model):
        """
        A Mixin that adds basic publishing info
        """
        status = models.IntegerField(
            _(config['FIELDNAMES'].get('status', 'status')),
            choices=config['STATUS_CHOICES'],
            default=config['DEFAULT_STATUS'])
        pub_date = models.DateField(
            _(config['FIELDNAMES'].get('pub_date', 'publish date')),
            null=True,
            blank=True)
        pub_time = models.TimeField(_(config['FIELDNAMES'].get('pub_time', 'publish time')),
            null=True,
            blank=True)

        class Meta:
            abstract = True

        @property
        def published(self):
            """
            Shortcut to set the published status in the status field. Acts like a
            boolean.
            """
            return self.status == config['PUBLISHED_STATUS']

        @published.setter
        def set_published(self, value):
            """
            Set the status to the unpublished status or published status
            """
            if bool(value):
                self.status = config['PUBLISHED_STATUS']
                if not self.pub_date:
                    self.pub_date = datetime.datetime.now()
                    self.pub_time = datetime.datetime.now()
            else:
                self.status = config['UNPUBLISHED_STATUS']

        objects = PubWorkflowManager()
    return PubWorkflowMixin
