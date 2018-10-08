=====
django-wx
=====

django-wx is a simple Django app to conduct Web-based wechat. For each
question, visitors can choose between a fixed number of answers.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "wechat" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'wechat',
    ]

2. Include the wechat URLconf in your project urls.py like this::

    path('wx/', include('wechat.urls')),

3. Run `python manage.py migrate` to create the wechat models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a poll (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/wx/ to participate in the django-wx.
