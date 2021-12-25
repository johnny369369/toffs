#!/usr/bin/env python
# ! coding=utf-8
import requests, json,sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pysnooper
from Params import Params
from mylog import mylogger
from aws_api import Aws_api 
from toffs_api import Toffs_api
from dateutil.tz import tzutc
import yaml
import datetime
import time
scpipts_path = os.getcwd()
#ssl dir 
cert_path = 'your ssl dir'

class Main:

     def __init__(self):
         self.toffs_token_dict = {'token': 'your token', 'email': 'you email','account_id':'you id'}
         self.init_class_params = Params()
         self.init_Toffs = Toffs_api(toffs_token=self.toffs_token_dict['token'],toffs_email=self.toffs_token_dict['email'],toffs_account_id=self.toffs_token_dict['account_id'])
         self.aws = Aws_api()

     def add_domain_to_toffs(self):
         '''
         create_domain_pad    需要传入字典格式数据 
         create_domain_pad   调用API接口POST添加PAD
         '''
         print(self.init_class_params.display(f'域名默认读取的是这个文件{scpipts_path}/domain_list','yellow'))
         select_website = self.select_website_list() 
         select_iplist = self.read_upstream_ip()
         for domain in open('./domain_list','r',encoding='utf-8').read().splitlines():
             data = {
                    'pad_aliases':f'{domain},*.{domain}',
                    'customer_brand':select_website,
                    'upstream_server':str(select_iplist),
                    'pad_name':domain.replace('.','_'),
                    'listen_http_ports':80,
                    'listen_https_ports':"443,9003",
                    'ssl_certificate_crt':self.read_domain_crt(domain=domain),
                    'ssl_certificate_key':self.read_domain_key(domain=domain)
                     }
             result = self.init_Toffs.create_domain_pad(data=data)
             #result = {'success':True,'result':{'pad_cname':'qg7dbh6ihizl.cdndd.net.'}}
             if result['success'] == True:
                update_domain_status = self.update_pad_status(status=1,pad_id=result['result']['id'])
                if update_domain_status['success'] == True or update_domain_status['success'] == 'true':
                   print(self.init_class_params.display(f'时间:{self._Get_date()}----------域名:{domain}添加到TOFFS成功','green'))
                   mylogger.info(f'域名:{domain}添加到TOFFS成功')
                else:
                   print(self.init_class_params.display(f'时间:{self._Get_date()}----------域名:{domain}添加到TOFFS失败:{update_domain_status}','red'))
                   mylogger.error(f'域名:{domain}添加到TOFFS失败')
                time.sleep(5)
                #查看AWS域名信息
                get_aws_domain_hosted_id = self.aws.list_hosted_zone_by_name(domain=f'{domain}')
                if len(get_aws_domain_hosted_id) >= 1: 
                   #获取域名hosted_id
                   domain_hosted_zone_id = get_aws_domain_hosted_id['HostedZones'][0]['Id'].split("/")[2] 
                   #获取域名记录列表
                   get_domain_hosted_records = self.aws.list_resource_record_sets(host_id=domain_hosted_zone_id) 
                   for record in get_domain_hosted_records:
                       if record['Name'] == f'{domain}.' and  record['Type'] == 'A':
                          #print(record['Name'],record['Type'],record['TTL'],record['ResourceRecords'][0]['Value'])
                          response = self.exec_aws_new_domain_records(domain=record['Name'],
                                                                         record_type=record['Type'],
                                                                         ttl=record['TTL'],
                                                                         value=record['ResourceRecords'][0]['Value'],
                                                                         action='DELETE',
                                                                         host_id=domain_hosted_zone_id)
                          if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                             print(self.init_class_params.display(f'时间:{self._Get_date()}----------域名:{domain}删除默认添加AWS-A-记录成功','green'))
                          else:
                             print(self.init_class_params.display(f'时间:{self._Get_date()}----------域名:{domain}删除默认添加AWS-A-记录失败:{response}','red'))

                       elif record['Name'] == f'\\052.{domain}.':
                            #print(record['Name'],record['Type'],record['TTL'],record['ResourceRecords'][0]['Value'])
                            response = self.exec_aws_new_domain_records(domain=record['Name'],
                                                                         record_type=record['Type'],
                                                                         ttl=record['TTL'],
                                                                         value=record['ResourceRecords'][0]['Value'],
                                                                         action='DELETE',
                                                                         host_id=domain_hosted_zone_id)
                            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                               print(self.init_class_params.display(f'时间:{self._Get_date()}----------{domain}删除默认添加AWS-CNAME记录成功','green'))
                            else:
                               print(self.init_class_params.display(f'时间:{self._Get_date()}----------{domain}删除默认添加AWS-CNAME记录失败:{response}','red'))
                   else:
                       print(self.init_class_params.display(f'时间:{self._Get_date()}----------域名配置信息为如下:','green'))
                       print(f'时间:{self._Get_date()}----------域名:{domain}     CNAME记录值为:' + result['result']['pad_cname'])
                       response_a = self.exec_aws_new_domain_records(domain=domain,
                                                             record_type='A',
                                                             ttl=300,
                                                             value=self.get_cname_values(cname_record_value=result['result']['pad_cname']),
                                                             action='CREATE',
                                                             host_id=domain_hosted_zone_id)
                       if response_a['ResponseMetadata']['HTTPStatusCode'] == 200:
                          print(self.init_class_params.display(f'时间:{self._Get_date()}----------{domain}创建AWS-A-记录成功','green'))
                       else:
                          print(self.init_class_params.display(f'时间:{self._Get_date()}----------{domain}创建AWS-A记录失败:{response_a}','red'))
                       response_cname = self.exec_aws_new_domain_records(domain=f'*.{domain}',
                                                                         record_type='CNAME',
                                                                          ttl=300,
                                                                          value=result['result']['pad_cname'],
                                                                          action='CREATE',
                                                                          host_id=domain_hosted_zone_id)
                       if response_cname['ResponseMetadata']['HTTPStatusCode'] == 200:
                          print(self.init_class_params.display(f'时间:{self._Get_date()}----------{domain}创建AWS-CANME记录成功','green'))
                          print('我是分隔符'.center(190, '='))
                       else:
                          print(self.init_class_params.display(f'时间:{self._Get_date()}----------{domain}创建AWS-CNAME记录失败:{response_cname}','red'))
                else:
                   print(self.init_class_params.display('时间:{self._Get_date()}---------数据返回为空,请检查域名是否添加到AWS','red'))
             else:
                 print(self.init_class_params.display(f'时间:{self._Get_date()}---------{domain}添加到Toffs失败:{result}','red'))

     def exec_aws_new_domain_records(self,domain=None,record_type=None,ttl=None,value=None,action=None,host_id=None):     
         response = self.aws.change_resource_record_sets(
                    HostedZoneId=host_id,
                    ChangeBatch={
                        'Comment': 'Modify domain name record',
                         'Changes':[
                                   {
                                    'Action': action,  
                                    'ResourceRecordSet': {
                                             'Name':f'{domain}',
                                             'Type':record_type,
                                             'TTL':ttl,
                                              'ResourceRecords':[
                                               {
                                                'Value':value
                                                },
                                            ],
                                        },
                                   },
                                ],
                       }
         )
         return response
     def update_pad_status(self,status=None,pad_id=None):
         '''
         更新PAD状态
         0 = pending
         1 = release 
         5 = stop
         4 = delete 
         '''
         result = self.init_Toffs.update_pad_status_info(status=status,pad_id=pad_id) 
         return result

     def show_pad_config(self): 
         '''
         显示PAD_CONFIG_INFO
         '''
         select_domain = self.init_class_params.check_input('输入你要查询的域名')
         get_domain_pad_id = self.get_pad_info(domain=select_domain)
         pad_id = get_domain_pad_id['result']['id']
         result = self.get_config_info(pad_id=pad_id) 
         for key,value in result['result'].items():
             if key in ['ssl_certificate_crt','ssl_certificate_key'] or value == None:
                pass 
             else:             
                print(self.init_class_params.display(f'{key}={value}','green').center(10,'-'))
            
     def get_cname_values(self,cname_record_value=None):
         '''
         域名添加到TOFFS成功后返回的CNAME值,获取该值的CANME记录的IP给域名加上@记录
         '''
         import socket
         ip_address = socket.getaddrinfo(cname_record_value, 'http')
         return ip_address[0][4][0]
          
     def select_website_list(self):
         '''
         选择站点，对应TOFFS后台的Customer Brand

         '''
         #生成站点BRAND菜单
         get_websiteList = self.get_brand_listInfo()
         website_dict = {}
         for i in enumerate(get_websiteList['result']):
             i_str = str(i[0])
             website_dict[i_str] = i[1]
         select_website = self.init_class_params.check_menu_dict(website_dict,'你的站点')
         return website_dict[select_website]
         
     def refresh_brand(self):
         '''
         先获取TOFSS配置的BRAND有那些,然后根据自己的站点品牌名刷新
         '''
         #获取BRAND-LIST
         result = self.get_brand_listInfo()         
         brand_dict = {}
         for i in enumerate(result['result']):
             i_str = str(i[0])
             brand_dict[i_str] = i[1] 
         select_website = self.init_class_params.check_menu_dict(brand_dict,'你刷新的站点')
         request_result = self.init_Toffs.refresh_Toffs_cache_brand(brand=brand_dict[select_website])
         website = brand_dict[select_website]
         if request_result['success'] == True:
            print(f'时间:{self._Get_date()}:Toffs_cdn站点:{website}刷新成功,返回日志为:{request_result}')
         elif request_result['success'] == False:
            print(f'时间:{self._Get_date()}:Toffs_cdn站点:{website}刷新失败,返回日志为:{request_result}')
         else:
            print(f'时间:{self._Get_date()}:{request_result}')

     def get_brand_listInfo(self):
         '''
         请求方法
         brand/account/account_id?page=1&per_page=50
         每次会请求TOFFS-API获取到最新的站点名(产品号(Customer Brand))
         '''
         result  = self.init_Toffs.get_brand_List()
         #print(result['result'])
         return result

     def show_brand_list(self):
         '''
         展示BRAND_LIST
         '''
         result = self.get_brand_listInfo()
         for i in result['result']:
             print(i.center(20))

     def get_config_info(self,pad_id=None):
         '''
         获取域名配置信息
         '''
         #get_pad_id = self.get_pad_info(domain=domain)
         #pad_id = get_pad_id['result']['id']
         result = self.init_Toffs.get_pad_domain_config(pad_id=pad_id)
         return result
       
     def refresh_domain_cache(self):
         '''
         刷新域名PAD缓存
         ''' 
         select_domain = self.init_class_params.check_input('输入你要刷新的域名')
         get_domain_pad_info = self.get_pad_info(domain=select_domain)
         #print(get_domain_pad_info['result']['id'])
         result = self.init_Toffs.refresh_pad_cache(pad_id=get_domain_pad_info['result']['id'])
         if result['success'] == True:
            print(self.init_class_params.display(f'时间:{self._Get_date()}----------:域名:{select_domain}缓存刷新成功','green'))
         else:
            print(self.init_class_params.display(f'时间:{self._Get_date()}----------:域名:{select_domain}缓存刷新失败','red'))
         
     def get_pad_info(self,domain=None):
         '''
         获取域名PAD_info信息  
         '''
         result = self.init_Toffs.get_pad_info(domain=domain)
         return result

     def show_pad_info(self):
         '''
         获取PAD基础信息
         '''
         select_domain = self.init_class_params.check_input('输入你要查询的域名')
         result = self.get_pad_info(domain=select_domain)
         #print(result['result'])
         for key,value in result['result'].items():
             print(f'{key}={value}')

     def update_domain_ssl(self):
         '''
         更新域名证书
         '''
         for domain in open('./domain_list','r',encoding='utf-8').read().splitlines():
             get_toffs_pad_info = self.get_pad_info(domain=domain)
             ssl_data = {
                        'pad_id':get_toffs_pad_info['result']['id'],
                        'ssl_certificate_crt':self.read_domain_crt(domain=domain),
                        'ssl_certificate_key':self.read_domain_key(domain=domain)
                        }
             result = self.init_Toffs.update_domain_sslcrt(**ssl_data)
             if result['success'] == True:
                update_domain_status = self.update_pad_status(status=1,pad_id=get_toffs_pad_info['result']['id'])
                if update_domain_status['success'] == True or update_domain_status['success'] == 'true':
                   print(f'时间:{self._Get_date()}----------:{domain}证书更新状态成功,返回日志:{update_domain_status}')
                   print('我是分隔符'.center(190, '='))
                else:
                   print(f'时间:{self._Get_date()}----------:{domain}证书更新状态失败,返回日志:{update_domain_status}') 
             elif result['success'] == False:
                print(f'时间:{self._Get_date()}----------:{domain}证书更新失败,返回日志:{result}')
             else:
                print(result)

     def read_domain_crt(self,domain=None):
         '''
         读取证书CRT
         '''
         domainCrt = self.find(f'{domain}.crt',cert_path)
         with open(f'{domainCrt}','r') as fcrt:
              domaincrt = fcrt.read()
              return domaincrt

     def read_domain_key(self,domain=None):
         '''
         读取域名KEY
         '''
         domainKey = self.find(f'{domain}.key',cert_path)
         with open(f'{domainKey}','r') as fkey:
              domainkey = fkey.read()
              return domainkey

     def _Get_date(self):
        '''获取当前时间'''
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

     def read_upstream_ip(self):
         '''
         选择回源IP  新增和删除都可以直接在字典删除
         多个回源的产品的NGINX-VIP可以自己新增KEY-VALUE
         '''
         nginx_ip_dict = {
                         'NGINX_VIP_IP'   : 'your ip',
                         }
         ip_dict = {}
         for i in enumerate(nginx_ip_dict.keys()):
             i_str = str(i[0])
             ip_dict[i_str] = i[1]
         select_upstream = self.init_class_params.check_menu_dict(ip_dict,'你的回源VIP')
         vip_nginx = ip_dict[select_upstream]
         return nginx_ip_dict[vip_nginx]

     def find(self,name,cert_path):
         '''
         用于查找目录及子目录下证书路径
         '''
         for root, dirs, files in os.walk(cert_path):
             if name in files:
                return os.path.join(root,name)

     def toffs_menu(self):
         menu_dict = {'1':'刷新CDN站点',
                      '2':'添加域名',
                      '3':'获取Brand-List',
                      '4':'获取PAD_INFO',
                      '5':'查看域名PAD配置信息',
                      '6':'更新域名证书',
                      '7':'刷新域名缓存'
                     }
         select_operating = self.init_class_params.check_menu_dict(menu_dict,'你的操作')
         if select_operating == '1':
            self.refresh_brand()
         elif select_operating == '2':
            self.add_domain_to_toffs()
         elif select_operating == '3':
              self.show_brand_list()
         elif select_operating == '4':
              self.show_pad_info()
         elif select_operating == '5':
              self.show_pad_config()
         elif select_operating == '6':
              self.update_domain_ssl()
         elif select_operating == '7':
              self.refresh_domain_cache()

if __name__ == '__main__':
    '''
    https://portal.toffstech.com/captcha/TxSli2UCD07VC5t.png?reload=随机     -----TOFFS 登录验证码
    '''
    start = Main()
    start.toffs_menu()
