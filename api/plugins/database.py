#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This is the ES library for Apache Kibble.
It stores the elasticsearch handler and config options.
"""


# Main imports
import re
#import aaa
import elasticsearch

from ndicts import NestedDict

class _KibbleESWrapper(object):
    """
       Class for rewriting old-style queries to the new ones,
       where doc_type is an integral part of the DB name
    """
    def __init__(self, ES):
        self.ES = ES

    def get(self, index, doc_type, id):
        return self.ES.get(index = index+'_'+doc_type, doc_type = '_doc', id = id)
    def exists(self, index, doc_type, id):
        return self.ES.exists(index = index+'_'+doc_type, doc_type = '_doc', id = id)
    def delete(self, index, doc_type, id):
        return self.ES.delete(index = index+'_'+doc_type, doc_type = '_doc', id = id)
    def index(self, index, doc_type, id, body):
        return self.ES.index(index = index+'_'+doc_type, doc_type = '_doc', id = id, body = body)
    def update(self, index, doc_type, id, body):
        return self.ES.update(index = index+'_'+doc_type, doc_type = '_doc', id = id, body = body)
    def scroll(self, scroll_id, scroll):
        return self.ES.scroll(scroll_id = scroll_id, scroll = scroll)
    def delete_by_query(self, **kwargs):
        return self.ES.delete_by_query(**kwargs)
    def search(self, index, doc_type, size = 100, scroll = None, _source_include = None, body = None):
        return self.ES.search(
            index = index+'_'+doc_type,
            doc_type = '_doc',
            size = size,
            scroll = scroll,
            _source_include = _source_include,
            body = body
            )
    def count(self, index, doc_type = '*', body = None):
        return self.ES.count(
            index = index+'_'+doc_type,
            doc_type = '_doc',
            body = body
            )

class _KibbleESWrapperSeven(object):
    """
       Class for rewriting old-style queries to the >= 7.x ones,
       where doc_type is an integral part of the DB name and NO DOC_TYPE!
    """
    def __init__(self, ES):
        self.ES = ES

    def get(self, index, doc_type, id):
        return self.ES.get(index = index+'_'+doc_type, id = id)
    def exists(self, index, doc_type, id):
        return self.ES.exists(index = index+'_'+doc_type, id = id)
    def delete(self, index, doc_type, id):
        return self.ES.delete(index = index+'_'+doc_type, id = id)
    def index(self, index, doc_type, id, body):
        return self.ES.index(index = index+'_'+doc_type, id = id, body = body)
    def update(self, index, doc_type, id, body):
        return self.ES.update(index = index+'_'+doc_type, id = id, body = body)
    def scroll(self, scroll_id, scroll):
        return self.ES.scroll(scroll_id = scroll_id, scroll = scroll)
    def delete_by_query(self, **kwargs):
        return self.ES.delete_by_query(**kwargs)
    def search(self, index, doc_type, size = 100, scroll = None, _source_include = None, body = None):
        return self.ES.search(
            index = index+'_'+doc_type,
            size = size,
            scroll = scroll,
            _source_includes = _source_include,
            body = body
            )
    def count(self, index, doc_type = '*', body = None):
        return self.ES.count(
            index = index+'_'+doc_type,
            body = body
            )

class _KibbleESWrapperEight(_KibbleESWrapperSeven):
    def __init__(self, ES):
        super().__init__(ES)
        # to replace key in body in queries
        self.replace = {'interval': 'calendar_interval'} # or fixed_interval

    def index(self, index, doc_type, id, body):
        if body is not None:
            body = self.ndict_replace(body, self.replace)
        return self.ES.index(index = index+'_'+doc_type, id = id, body = body)
    def update(self, index, doc_type, id, body):
        if body is not None:
            body = self.ndict_replace(body, self.replace)
        return self.ES.update(index = index+'_'+doc_type, id = id, body = body)

    def search(self, index, doc_type, size = 100, scroll = None, _source_include = None, body = None):
        if body is not None:
            body = self.ndict_replace(body, self.replace)
        if 'size' in body:
            print("WARNING duplicate size: body size %s and size param: %s" % (body['size'], size) )
            #del body['size']
        return self.ES.search(
            index = index+'_'+doc_type,
            size = size,
            scroll = scroll,
            _source_includes = _source_include,
            body = body
            )
    def count(self, index, doc_type = '*', body = None):
        if body is not None:
            body = self.ndict_replace(body, self.replace)
        return self.ES.count(
            index = index+'_'+doc_type,
            body = body
            )

    def ndict_replace(self, dict, replace):
        #print("original body/dict : %s." %(dict) )
        ndict = NestedDict(dict)
        new_nd = NestedDict()
        for key, value in ndict.items():
            # get(k,k) with second parameter as default return value
            result = tuple( replace.get(k, k) for k in key )
            #print("replace %s matched in key %s " %(key, result) )
            new_key = result
            new_nd[new_key] = value
        new_dict =  new_nd.to_dict();
        #print("replaced body/dict: %s." %(new_dict) )
        return new_dict

class KibbleDatabase(object):
    def __init__(self, config):
        self.config = config
        self.dbname = config['elasticsearch']['dbname']

        defaultELConfig = {
            'host': config['elasticsearch']['host'],
            'port': int(config['elasticsearch']['port']),
        }
        versionHint = config['elasticsearch']['versionHint']
        if (versionHint >= 7):
            defaultELConfig['scheme'] = 'https' if (config['elasticsearch']['ssl']) else 'http'
            defaultELConfig['path_prefix'] = config['elasticsearch']['uri'] if 'uri' in config['elasticsearch'] else ''
        else:
           defaultELConfig['use_ssl'] =  config['elasticsearch']['ssl']
           defaultELConfig['verify_certs']: False
           defaultELConfig['url_prefix'] = config['elasticsearch']['uri'] if 'uri' in config['elasticsearch'] else ''
           defaultELConfig['http_auth'] = config['elasticsearch']['auth'] if 'auth' in config['elasticsearch'] else None

        self.ES = elasticsearch.Elasticsearch([ defaultELConfig ],
                max_retries=5,
                retry_on_timeout=True
            )

        # IMPORTANT BIT: Figure out if this is ES < 6.x, 6.x or >= 7.x.
        # If so, we're using the new ES DB mappings, and need to adjust ALL
        # ES calls to match this.
        self.ESversion = int(self.ES.info()['version']['number'].split('.')[0])
        if self.ESversion >= 8:
             self.ES = _KibbleESWrapperEight(self.ES)
        elif self.ESversion >= 7:
            self.ES = _KibbleESWrapperSeven(self.ES)
        elif self.ESVersion >= 6:
            self.ES = _KibbleESWrapper(self.ES)
