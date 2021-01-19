# National Environmental Methods Index

Search interface for www.nemi.gov, written in Django.


## Local Development

Place local settings in `nemi/nemi_project/settings/local.py`. Here's a basic
example that connects to the dev database:

```python
#pylint: disable=W0401,W0614
from .dev import *

# Should be of form: oracle://USER:PASSWORD@HOST:PORT/NAME
# To override in environment, set DATABASE_URL environment variable.
# Add the if statement so that tests can be run if JENKINS_URL is defined
if not os.getenv('JENKINS_URL', False):
    DATABASES['default'] = dj_database_url.config(default='oracle://USER:PASSWORD@HOST:PORT/NAME')

# Make this unique, and don't share it with anybody.
# Get the dev SECRET_KEY from the live environment.
SECRET_KEY = ''

# Note that using this seriously slows down page rendering and if set to True
# the Browse page will not work.
#show_debug_toolbar(globals())
```

### Building for local development
Create a virtualenv and install the python dependencies:
```
% virtualenv --python=python3 env
% env/bin/pip install -r requirements.txt
```

The style sheets must be built as well. In order to build the style sheets from Sass. You must have
the compass Gem installed as follows:
```
% cd nemi/compass
% gem install -i Gem compass -v 0.12.7
```
To build the style sheets execute:
```
% cd nemi/compass (if not there already)
% ./compass.sh compile
```

### Running development server
```
% cd nemi
% ./manage.py runserver
```

### Running python tests
A local sqlite database is used to perform testing on the python code.
```
% cd nemi
% DBA_SQL_DJANGO_ENGINE=django.db.backends.sqlite3 JENKINS_URL=anything ../env/bin/python ./manage.py jenkins --enable-coverage
```

### Creating database migrations

The NEMI database is Oracle-based, and not originally managed by Django migrations. As a result,
the column types do not necessarily map to what the Django ORM's Oracle driver would choose.
Therefore, it is useful to inspect the SQL that Django's `makemigrations` management command
produces before executing it against a dev database.

For example, to auto-create a migration corresponding to model changes in an app, run:

```bash
python manage.py makemigrations <app-name>
```

Then, inspect the SQL statements that would be executed by that migration:

```bash
python manage.py sqlmigrate <app-name> <migration-name>
```

If the SQL looks correct and is consistent with the patterns used in the NEMI database, it may be
executed against a dev database:

```bash
python manage.py migrate
```

If another representation of the model change is more appropriate than the auto-created SQL, you
may edit the auto-created migration and use
[raw SQL](https://docs.djangoproject.com/en/2.1/ref/migration-operations/#runsql). For example,
this migration changes the column type of a field and notifies the migration system of the field
change it corresponds to:

```python
class Migration(migrations.Migration):
    dependencies = [
        ('common', '0002_auto_20180926_1147')
    ]
    operations = [
        migrations.RunSQL(
            'ALTER TABLE "METHOD" MODIFY "SOURCE_METHOD_IDENTIFIER" VARCHAR2(45);',
            state_operations=[
                migrations.AlterField(
                    model_name='method',
                    name='source_method_identifier',
                    field=models.CharField(max_length=45, unique=True, verbose_name='method number/identifier')
                )
            ]
        )
    ]
```
