

import os
import requests
from requests.structures import CaseInsensitiveDict
import json
import time
import logging

console = logging.StreamHandler()
tx_logger = logging.getLogger('tx3')
tx_logger.addHandler(console)


class _tx_request:

    def __init__(self,tx_token):
        self.headers = CaseInsensitiveDict()
        self.headers["Accept"] = "application/vnd.api+json"
        # self.headers["Content-Type"] = "application/vnd.api+json"
        self.headers["Authorization"] = "Bearer " + tx_token
        self.api_base="https://rest.api.transifex.com/"

    def post(self,url,payload):
        header=dict(self.headers)
        header["Content-Type"] = "application/vnd.api+json"

        # print(json.dumps(payload,indent=2))
        resp = requests.post(self.api_base + url, data=json.dumps(payload), headers=header)
        # print(json.dumps(resp.json(),indent=2))
        resp.raise_for_status()
        try:
            return resp.json()
        except:
            return resp.text

    def get(self,url):
        # print("GET")
        resp = requests.get(self.api_base + url, headers=self.headers)
        # print(json.dumps(resp.json(),indent=2))
        resp.raise_for_status()
        try:
            return resp.json()
        except:
            return resp.text

    def get_url(self,url):
        # print("GET_URL")
        resp = requests.get(url, headers=self.headers)
        # print(json.dumps(resp.json(),indent=2))
        resp.raise_for_status()
        try:
            return resp.json()
        except:
            return resp.text

    def delete(self,url):
        resp = requests.delete(self.api_base + url, headers=self.headers)
        resp.raise_for_status()
        try:
            return resp.json()
        except:
            return resp.text

    def delete_pl(self,url,payload):
        header=dict(self.headers)
        header["Content-Type"] = "application/vnd.api+json"
        resp = requests.delete(self.api_base + url, data=json.dumps(payload), headers=header)
        resp.raise_for_status()
        try:
            return resp.json()
        except:
            return resp.text

    def download(self,type,body,path):

        header=dict(self.headers)
        header["Content-Type"] = "application/vnd.api+json"
        down = requests.post(self.api_base + type,data=json.dumps(body) ,headers=header)
        print(down.status_code, down.json())
        if down.status_code <= 400:
            status_id = down.json()['data']['id']
            # print(down.json())
            stat=type+"/"+status_id
            f=requests.get(self.api_base + stat, headers=self.headers)
            # print(f.headers)

            while 'Content-disposition' not in f.headers:
                time.sleep(0.5)
                f=requests.get(self.api_base + stat, headers=self.headers)

            with open(path, 'wb') as transfile:
                for line in f.iter_content():
                    transfile.write(line)
        else:
            tx_logger.info(str(down.status_code)+" Error downloading "+path)

    def upload(self,type,payload,content):

        header=dict(self.headers)
        tx_logger.debug(header,payload)
        up = requests.post(self.api_base + type, data=payload,files=content, headers=header)
        tx_logger.debug(up.json())

        if not up.raise_for_status():
            status_id = up.json()['data']['id']
            # tx_logger.debug(down.json())
            stat=type+"/"+status_id
            f=requests.get(self.api_base + stat, headers=self.headers)
            tx_logger.info(f.headers)

        else:
            tx_logger.info(up.status_code+" Error uploading file")


class language:
    def __init__(self,lang):
        self.details=lang
        self.id=lang['id']
        self.attributes=lang['attributes']
        self.name=self.attributes['name']
        self.code=self.attributes['code']


class resource:
    def __init__(self,res,txr):
        self.details=res
        self.id=res['id']
        self.attributes=res['attributes']
        self.name=self.attributes['name']
        self.slug=self.attributes['slug']
        self.txr=txr
        self.project=res['relationships']['project']['data']['id']
        self.stats={}
        self.trans={}

    def pull(self,lang,path,mode="onlytranslated"):

        payload = {"data": {
                                "attributes": {
                                    "mode": mode
                                },                            
                                "relationships": {
                                    "language": {
                                        "data": {
                                            "id": "l:" + lang,
                                            "type": "languages"
                                        }
                                    },
                                    "resource": {
                                        "data": {
                                            "id": self.id,
                                            "type": "resources"
                                        }
                                    }
                                }, 
                                "type": "resource_translations_async_downloads"
                                }
                            }

        # print(payload)
        tx_logger.info("Downloading " + path +" ...")
        self.txr.download("resource_translations_async_downloads",payload,path)
        tx_logger.info("done.")

    def pull_source(self,path):

        payload = {"data": {"attributes":{},"relationships": {
                                    "resource": {
                                        "data": {
                                            "id": self.id,
                                            "type": "resources"
                                        }
                                    }
                                }, "type": "resource_strings_async_downloads"}
                            }
        # print(payload)
        tx_logger.info("Downloading " + path + " ...")
        self.txr.download("resource_strings_async_downloads",payload,path)
        tx_logger.info("done.")

    def push(self,path,lang=''):
        payload = {'resource':  self.id}
        type="resource_strings_async_uploads"
        if lang:
            payload['language']='l:'+lang
            type="resource_translations_async_uploads"
        content = {('content', open(path,'rb'))}

        tx_logger.info("Pushing " + path + " to transifex... ("+self.slug+")")
        self.txr.upload(type,payload,content)
        tx_logger.info("done.")

    def delete(self):
        tx_logger.info("Deleting " + self.slug + " ...")
        self.txr.delete("resources/"+self.id)
        tx_logger.info("done.")

    def __language_stats(self,lang=''):
        l=''
        if lang != '':
            l='&filter[language]=l:' + lang
        stats="resource_language_stats?filter[project]="+self.project+"&filter[resource]=" + self.id + l
        st = self.txr.get(stats)
        for s in st['data']:
            statlang = s['relationships']['language']['data']['id'].split(':')[1]
            if statlang not in self.stats:
                self.stats[statlang] = s['attributes']
        if lang != '':
            return self.stats[lang]
        else:
            return self.stats

    def language_stats(self,lang):
        if lang != '':
            if lang in self.stats:
                return self.stats[lang]
            else:
                return self.__language_stats(lang)
        else:
            return self.__language_stats(lang)
        
    def set_language_stats(self,lang,stats):
        self.stats[lang] = stats

    def __translations(self,lang):
        l=''
        if lang != '':
            l='&filter[language]=l:' + lang
            trans="resource_translations?include=resource_string&filter[resource]=" + self.id + l
            st = self.txr.get(trans)

            if lang not in self.trans:
                # store the full translations object
                self.trans[lang] = st

            return self.trans[lang]


    def translations(self,lang):
        if lang != '':
            if lang in self.trans:
                return self.trans[lang]
            else:
                return self.__translations(lang)
        else:
            return self.__translations(lang)
            


class project:
    def __init__(self,proj,txr):
        self.details=proj
        self.id=proj['id']
        self.attributes=proj['attributes']
        self.name=self.attributes['name']
        self.slug=self.attributes['slug']
        self.txr=txr
        self._resources=[]
        self._languages=[]
        # self._details={}
        self.stats={}

    def __resources(self):
        if self._resources == []:
            tx_logger.info("Fetching resources for project '"+self.name+"'...")
            resources="resources?filter[project]=" + self.id
            ress = self.txr.get(resources)
            for r in ress['data']:
                self._resources.append(resource(r,self.txr))
            while ress['links']['next']:
                # print(ress['links']['next'])
                ress = self.txr.get_url(ress['links']['next'])
                for r in ress['data']:
                    self._resources.append(resource(r,self.txr))
            tx_logger.info("done.")

    def resources(self):
        self.__resources()
        rs = []
        for r in self._resources:
            rs.append(r)
        return rs

    def resource(self, res):
        self.__resources()
        for r in self._resources:
            if r.slug == res:
                return r
        return None


    def delete_resource(self, res):
        self.__resources()
        for r in self._resources:
            if r.slug == res:
                r.delete()
                self._resources == []
                print("reset resources")
                self.__resources()

    def __languages(self):
        if self._languages == []:
            tx_logger.info("Fetching languages for project '"+self.name+"'...")
            languages="projects/" + self.id + "/languages"
            langs = self.txr.get(languages)
            for l in langs['data']:
                self._languages.append(language(l))
            # while langs['links']['next']:
            #     langs = self.txr.get_url(lannguage['links']['next'])
            #     for l in langs['data']:
            #         self._languages.append(language(l))
            tx_logger.info("done.")

    def add_language(self, lang_id):
        self.__languages()
        for l in self._languages:
            if l.id == lang_id:
                tx_logger.info("Language "+l.code+" already exists on project.")
                return
        # language is not already part of project, so add it
        tx_logger.info("Adding language "+lang_id+" to project.")
        payload = {
                        "data": [
                            {
                            "id": lang_id,
                            "type": "languages"
                            }
                        ]
                    }
        linked_languages_api = "projects/" + self.id + "/relationships/languages"
        
        create_lang=self.txr.post(linked_languages_api,payload)
        #reset project languages
        self._languages=[]
        self.__languages()

    def delete_language(self, lang_id):
        self.__languages()
        for l in self._languages:
            if l.id == lang_id:
                tx_logger.info("Removing language "+l.code+" from project.")
                payload = {
                                "data": [
                                    {
                                    "id": lang_id,
                                    "type": "languages"
                                    }
                                ]
                            }
                linked_languages_api = "projects/" + self.id + "/relationships/languages"
                delete_lang=self.txr.delete_pl(linked_languages_api,payload)
                #reset project languages
                self._languages=[]
                self.__languages()
                return

        tx_logger.info("Language "+lang_id+" does not exist on project.")

    def language(self, lang):
        self.__languages()
        for l in self._languages:
            if l.code == lang:
                return l

    def languages(self):
        self.__languages()
        ls = []
        for l in self._languages:
            ls.append(l)
        return ls

    def language_stats(self,lang=''):
        l_message=''
        l=''
        if lang != '':
            l='&filter[language]=l:' + lang
            l_message=" language '"+lang+"'"
        tx_logger.info("Fetching language stats for project resources '"+self.name+"'"+l_message+"...")
        stats="resource_language_stats?filter[project]=" + self.id + l
        st = self.txr.get(stats)
        #print(st)
        for s in st['data']:
            statlang = s['relationships']['language']['data']['id'].split(':')[1]
            statres = s['relationships']['resource']['data']['id'].split(':')[5]
            if self.resource(statres):
                self.resource(statres).set_language_stats(statlang,s['attributes'])

            if statlang not in self.stats:
                self.stats[statlang] = s['attributes']
        while 'next' in st['links']:
            st = self.txr.get_url(st['links']['next'])
            for s in st['data']:
                statlang = s['relationships']['language']['data']['id'].split(':')[1]
                statres = s['relationships']['resource']['data']['id'].split(':')[5]
                if self.resource(statres):
                    self.resource(statres).set_language_stats(statlang,s['attributes'])
                if statlang not in self.stats:
                    self.stats[statlang] = s['attributes']
        if lang != '':
            return self.stats[lang]
        else:
            return self.stats

    def new_resource(self,name,slug,i18type,path='',categories=[]):
        payload={
                    "data": {
                        "attributes": {
                            "accept_translations": True,
                            "categories": categories,
                            "name": name,
                            "priority": "normal",
                            "slug": slug
                            },
                        "relationships": {
                            "i18n_format": {
                                "data": {
                                "id": i18type,
                                "type": "i18n_formats"
                                }
                            },
                            "project": {
                                "data": {
                                    "id": self.id,
                                    "type": "projects"
                                }
                            }
                        },
                        "type": "resources"
                    }
                }
        create_res=self.txr.post("resources",payload)
        new_resource= resource(create_res['data'],self.txr)
        self._resources.append(new_resource)
        # If a path has been provided, upload the file to the resource
        if path:
            new_resource.push(path)


class tx:
    def __init__(self,org,tx_token,log_level=20):
        # default log level is INFO

        self.org="o:"+org
        self.txr=_tx_request(tx_token)
        self._projects=[]

        tx_logger.setLevel(log_level)


    def __projects(self):
        if self._projects == []:
            tx_logger.debug("Fetching projects...")
            projects="projects?filter[organization]=" + self.org
            prjs = self.txr.get(projects)
            for p in prjs['data']:
                self._projects.append(project(p,self.txr))
            while prjs['links']['next']:
                prjs = self.txr.get_url(prjs['links']['next'])
                for p in prjs['data']:
                    self._projects.append(resource(p,self.txr))
            tx_logger.debug("done.")

    def projects(self):
        self.__projects()
        ps = []
        for p in self._projects:
            ps.append(p)
        return ps

    def project(self, proj):
        self.__projects()
        for p in self._projects:
            if p.slug == proj:
                return p

