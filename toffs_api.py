#!/usr/bin/env python
# ! coding=utf-8
import requests, json,sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pysnooper
from Params import Params
from mylog import mylogger
from aws_api import Aws_api 
from dateutil.tz import tzutc
import yaml
import datetime
scpipts_path = os.getcwd()
#SSL DIR
cert_path = 'your dir'

# @pysnooper.snoop()
class Toffs_api():

      def __init__(self,toffs_token=None,toffs_email=None,toffs_account_id=None):
          self.toffs_email= toffs_email
          self.toffs_token = toffs_token
          self.toffs_account_id = toffs_account_id
          self.toffs_host = 'https://api.toffstech.com'
          self.account = toffs_account_id
          self.headers={}
          self.headers['X-Auth-Email'] = self.toffs_email
          self.headers['X-Auth-Token'] = self.toffs_token
          self.aws = Aws_api()

      def get_pad_info(self,domain=None):
          '''
          获取域名PAD信息
          '''
          return_data = {}
          try:
             api_url = f'{self.toffs_host}/v1/pad/host/{domain}'
             response = requests.get(url=api_url,headers=self.headers).json()
          except Exception as e:
              return_data['success'] = False
              return_data['message'] = e.__str__()
              return return_data
          else:
              return  response
      def update_pad_status_info(self,status=None,pad_id=None):
          '''
          更新PAD状态
          '''
          return_data = {}
          try:
             api_url = f'{self.toffs_host}/v1/pad/status/{pad_id}'
             data = {'status':status}
             response = requests.put(url=api_url,headers=self.headers,data=data).json()
          except Exception as e:
              return_data['success'] = False
              return_data['message'] = e.__str__()
              return return_data
          else:
              return  response

      def get_pad_domain_config(self,pad_id=None):
          return_data = {}
          try:
             api_url = f'{self.toffs_host}/v1/pad/{pad_id}/pad_info'
             response = requests.get(url=api_url,headers=self.headers).json()
          except Exception as e:
              return_data['success'] = False
              return_data['message'] = e.__str__()
              return return_data
          else:
              return  response

      def get_toffs_pad_list(self,page_id=None):
          return_data = {}
          try:
              self.headers['X-Auth-Token'] = self.toffs_token
              api_url = f'{self.toffs_host}/v1/pads/account_id'
              data = {'page': page_id,'per_page':'50'}
              response = requests.get(url=api_url,data=data,headers=self.headers).json()
          except Exception as e:
              return_data['success'] = False
              return_data['message'] = e.__str__()
              return return_data
          else:
              return response

      def get_brand_List(self):
         return_data = {}
         try:
             api_url = f'{self.toffs_host}/v1/brands/account/account_id'
             data = {'page': '1','per_page':'50'}
             response = requests.get(url=api_url,data=data,headers=self.headers)
         except Exception as e:
             return_data['success'] = False
             return_data['message'] = e.__str__()
             return return_data
         else:
             return  response.json()

      def filter_response_data(self,product=None,domain=None):
          return_data = {}
          try:
              domain_cut = domain.split('.')
              for page_id in range(1, 10000):
                  requests_result = self.get_toffs_pad_list(page_id=page_id)
                  for site_info in requests_result['result']:
                      if (f'{product}_{domain_cut[0]}_{domain_cut[1]}') in site_info['pad_name']:
                         return site_info['id']
          except Exception as e:
              return_data['success'] = False
              return_data['message'] = e.__str__()
              return return_data

      def refresh_pad_cache(self,pad_id=None):
          return_data = {}
          try:
             api_url = f'{self.toffs_host}/v1/purgecache'
             data = {'pad_id':pad_id} 
             response = requests.post(url=api_url,headers=self.headers,data=data).json()
          except Exception as e:
             return_data['success'] = False
             return_data['message'] = e.__str__()
             return return_data
          else:
             return response

      def get_account_info(self):
          return_data = {}
          try:
              self.headers['X-Auth-Token'] = self.toffs_token
              api_url = f'{self.toffs_host}/v1/user/accounts'
              response = requests.get(url=api_url,headers=self.headers).json()
          except Exception as e:
              return_data['success'] = False
              return_data['message'] = e.__str__()
              return return_data
          else:
              return response

      def update_domain_sslcrt(self,**kwargs):
          return_data = {}
          try:
             data = {}
             data['ssl_enable'] = True
             data['http2'] = True
             data['ssl_force_redirect'] = True
             data['ssl_certificate_crt'] = kwargs['ssl_certificate_crt']
             data['ssl_certificate_key'] = kwargs['ssl_certificate_key']
             data['hsts_includesubdomains'] = 0
             data['hsts'] = False
             api_url = '{}/v1/pad/ssl/{}'.format(self.toffs_host,kwargs['pad_id'])
             response = requests.put(url=api_url,data=data,headers=self.headers).json()
          except Exception as e:
             return_data['success'] = False
             return_data['message'] = e.__str__()
             return return_data
          else:
              return response

      def refresh_Toffs_cache_brand(self,**kwargs):
          return_data = {}
          data = {'brand':kwargs['brand'],'account_id':self.toffs_account_id}
          try:
               api_url = f'{self.toffs_host}/v1/purgecache'
               response = requests.post(url=api_url,data=data,headers=self.headers)
          except Exception as e:
              return_data['success'] = False 
              return_data['message'] = e.__str__()
              return return_data
          else:
               return response.json() 

      def create_domain_pad(self,**kwargs):
           return_data = {}
           try:
              pad_data = {}
              pad_data['account_id'] =  self.account
              pad_data['ssl_certificate_crt'] = kwargs['data']['ssl_certificate_crt']
              pad_data['ssl_certificate_key'] = kwargs['data']['ssl_certificate_key']
              pad_data['pad_aliases'] =  kwargs['data']['pad_aliases']
              pad_data['customer_brand'] = kwargs['data']['customer_brand']
              pad_data['upstream_server'] = kwargs['data']['upstream_server']
              pad_data['pad_name'] = kwargs['data']['pad_name']
              pad_data['listen_http_ports'] = kwargs['data']['listen_http_ports'] if kwargs['data'].get('listen_http_ports') else 80
              pad_data['listen_https_ports'] = kwargs['data']['listen_https_ports'] if kwargs['data'].get('listen_https_ports') else "443,9003"
              pad_data['ssl_force_redirect'] = kwargs['data']['ssl_force_redirect'] if kwargs['data'].get('ssl_force_redirect') else True
              pad_data['upstream_scheme'] = kwargs['data']['upstream_scheme'] if kwargs['data'].get('upstream_scheme') else 'Https-Only'
              pad_data['ssl_enable'] = kwargs['data']['ssl_enable'] if kwargs['data'].get('ssl_enable') else True
              pad_data['upstream_method'] = kwargs['data']['upstream_method'] if kwargs['data'].get('upstream_method') else 1
              #pad_data['status'] = kwargs['data']['status'] if kwargs['data'].get('status') else 1
              api_url = f'{self.toffs_host}/v1/pad'
              response = requests.post(url=api_url,data=pad_data,headers=self.headers).json()
           except Exception as e:
              return_data['success'] = False
              return_data['message'] =  e.__str__()
              return return_data
           else:
              return response
