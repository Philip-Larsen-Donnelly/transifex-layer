

import os
import requests
from requests.structures import CaseInsensitiveDict
import json
import time


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
        resp = requests.get(self.api_base + url, headers=self.headers)
        # print(json.dumps(resp.json(),indent=2))
        resp.raise_for_status()
        try:
            return resp.json()
        except:
            return resp.text

    def get_url(self,url):
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

    def download(self,type,body,path):

        header=dict(self.headers)
        header["Content-Type"] = "application/vnd.api+json"
        down = requests.post(self.api_base + type,data=json.dumps(body) ,headers=header)
        # print(down.json())
        status_id = down.json()['data']['id']
        if not down.raise_for_status():
            # print(down.json())
            stat=type+"/"+status_id
            f=requests.get(self.api_base + stat, headers=self.headers)
            # print(f.headers)

            while 'Content-disposition' not in f.headers:
                time.sleep(2)
                f=requests.get(self.api_base + stat, headers=self.headers)

            with open(path, 'wb') as transfile:
                for line in f.iter_content():
                    transfile.write(line)
        else:
            print(down.status_code,"Error downloading",path)

    def upload(self,type,payload,content):

        header=dict(self.headers)
        print(header,payload)
        up = requests.post(self.api_base + type, data=payload,files=content, headers=header)
        print(up.json())
        status_id = up.json()['data']['id']

        if not up.raise_for_status():
            # print(down.json())
            stat=type+"/"+status_id
            f=requests.get(self.api_base + stat, headers=self.headers)
            print(f.headers)

        else:
            print(up.status_code,"Error uploading file")


class resource:
    def __init__(self,res,txr):
        self.res=res
        self.id=res['id']
        self.attributes=res['attributes']
        self.name=self.attributes['name']
        self.slug=self.attributes['slug']
        self.txr=txr
        self.project=res['relationships']['project']['data']['id']
        self.stats={}

    def pull(self,lang,path):

        payload = {"data": {"relationships": {
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
                                }, "type": "resource_translations_async_downloads"}
                            }
        # print(payload)
        print("Downloading",path,"...")
        self.txr.download("resource_translations_async_downloads",payload,path)
        print("done.")

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
        print("Downloading",path,"...")
        self.txr.download("resource_strings_async_downloads",payload,path)
        print("done.")

    def push(self,path,lang=''):
        payload = {'resource':  self.id}
        type="resource_strings_async_uploads"
        if lang:
            payload['language']='l:'+lang
            type="resource_translations_async_uploads"
        content = {('content', open(path,'rb'))}

        print("Pushing",path,"to transifex... ("+self.slug+")")
        self.txr.upload(type,payload,content)
        print("done.")

    def delete(self):
        print("Deleting",self.slug,"...")
        self.txr.delete("resources/"+self.id)
        print("done.")

    def language_stats(self,lang=''):
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




class project:
    def __init__(self,proj,txr):
        self.proj=proj
        self.id=proj['id']
        self.attributes=proj['attributes']
        self.name=self.attributes['name']
        self.slug=self.attributes['slug']
        self.txr=txr
        self._resources=[]
        self._details={}
        self.stats={}

    def __details(self):
        if self._details == {}:
            det="projects/" + self.id
            self._details = self.txr.get(det)['data']

    def details(self):
        self.__details()
        return self._details

    def __resources(self):
        if self._resources == []:
            print("Fetching resources for project '"+self.name+"'...")
            resources="resources?filter[project]=" + self.id
            ress = self.txr.get(resources)
            for r in ress['data']:
                self._resources.append(resource(r,self.txr))
            while ress['links']['next']:
                # print(ress['links']['next'])
                ress = self.txr.get_url(ress['links']['next'])
                for r in ress['data']:
                    self._resources.append(resource(r,self.txr))
            print("done.")


    def resources(self):
        self.__resources()
        rs = []
        for r in self._resources:
            rs.append(r.res)
        return rs

    def resource(self, res):
        self.__resources()
        for r in self._resources:
            if r.slug == res:
                return r

    def languages(self):
        lang="projects/" + self.id + "/languages"
        return self.txr.get(lang)

    def language_stats(self,lang=''):
        l=''
        if lang != '':
            l='&filter[language]=l:' + lang
        stats="resource_language_stats?filter[project]=" + self.id + l
        st = self.txr.get(stats)
        for s in st['data']:
            statlang = s['relationships']['language']['data']['id'].split(':')[1]
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
    def __init__(self,org,tx_token):

        self.org="o:"+org
        self.txr=_tx_request(tx_token)
        self._projects=[]


    def __projects(self):
        if self._projects == []:
            print("Fetching projects...")
            projects="projects?filter[organization]=" + self.org
            prjs = self.txr.get(projects)
            for p in prjs['data']:
                self._projects.append(project(p,self.txr))
            while prjs['links']['next']:
                prjs = self.txr.get_url(prjs['links']['next'])
                for p in prjs['data']:
                    self._projects.append(resource(p,self.txr))
            print("done.")

    def projects(self):
        self.__projects()
        ps = []
        for p in self._projects:
            ps.append(p.proj)
        return ps

    def project(self, proj):
        self.__projects()
        for p in self._projects:
            if p.slug == proj:
                return p
