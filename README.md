# transifex-layer
A simple python module to support interaction with the transifex API3

## Install with pip

```bash
pip install https://github.com/Philip-Larsen-Donnelly/translayer/archive/refs/heads/main.zip
```

> Tip - use `--upgrade` to get the latest:
>  ```
>  pip install --upgrade https://github.com/Philip-Larsen-Donnelly/translayer/archive/refs/heads/main.zip
>  ```

## Create a tx3 instance

```
from translayer import tx3

#create an instance of a transifex organisation (pass organisation slug and transifex API token)
org = "hisp-uio"
tx_token = os.getenv("TX_TOKEN")

tx = tx3.tx(org,tx_token)
```

## Projects

```
# get a list of the projects
projects = tx.projects()
for p in projects:
    print(p.name)

# get a specific project by slug
p_slug = "dhis-2-documentation-235"
project = tx.project(p_slug)
# print the attributes
print(project.name)
print(project.slug)
print(project.attributes)
print(project.details)

# get project languages
langs = project.languages()
for l in langs:
    print(l.code)

# get a specific language by code
l_code = "cs"
lang = project.language(l_code)
print(lang.name)

# add a new language to the project (by id)
l_id = "l:vi"
project.add_language(l_id)

# delete a language from the project (by id)
l_id = "l:vi"
project.delete_language(l_id)

# get project resources
resources = project.resources()
for r in resources:
    print(r.name)

# get a specific resource by slug
r_slug = "dhis2-who-data-quality-tool-guide-md"
resource = project.resource(r_slug)
print(resource.name)

```

## Resources
```

# get the language stats for a resource
l_stats = resource.language_stats("fr")
print(l_stats)
print(l_stats['translated_strings'])
print(l_stats['total_strings'])

# get the language stats for all languages
l_stats = resource.language_stats()
for s in l_stats:
    print(s)
    print(l_stats[s]['translated_strings'])
    print(l_stats[s]['total_strings'])

# get the language stats for the whole project
# (NOTE THESE DON'T SEEM CONSISTENT WITH THE TOTALS FROM ALL RESOURCES)
p_stats = project.language_stats()
for s in p_stats:
    print(s)
    print(p_stats[s]['translated_strings'])
    print(p_stats[s]['total_strings'])

# get the full translations object for a given language
translations = resource.translations("fr")

```

## Pushing and pulling translation files

```
# create a new resource if it doesn't exist
name="JUST_TEST2"
new_slug="just_test2-md"
i18n_format='GITHUBMARKDOWN'
path="my/file/path.md"
if not tx.project(pp).resource(new_slug):
   tx.project(pp).new_resource(name,slug,i18n_format,path)

# push a resource (source)
tx.project(pp).resource(new_slug).push(path)

# push localisation file
locale_path="my/file/path_fr.md"
l_code="fr"
tx.project(pp).resource(new_slug).push(locale_path,l_code)

# pull translation
tx.project(pp).resource(new_slug).pull(l_code,locale_path)

# pull source language
tx.project(pp).resource(new_slug).pull_source(path)
```

## Delete resources :caution:

```
# delete a resource
tx.project(pp).resource(new_slug).delete()
```
