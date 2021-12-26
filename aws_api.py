import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ParamValidationError

class Aws_api():
    
     def __init__(self):
        aws_access_key_id = 'your id'
        aws_secret_key = 'your key'
        account = 'route53'
        self.client = boto3.client(account,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_key)

     def get_hosted_zone(self,zone_id):
         try:
             response = self.client.get_hosted_zone(Id=zone_id)
         except Exception as e:
             return e.__str__() 
         else:
             return response
          
     def get_list_hosted_zones(self):
         '''
         获取AWS的列表域名信息
         id name CallerReference Config ResourceRecordSetCount等 
         '''
         data = {'MaxItems': '100'}
         zones = []
         def get_zones():
             response = self.client.list_hosted_zones(**data)
             zones.extend(response['HostedZones'])
             if response['IsTruncated']:
                data['Marker'] = response['NextMarker']
                get_zones()

         get_zones()
         return zones
         #for i in response["HostedZones"]:
         #    print(i)
         #    if i['Name'] == f'{domain}.':
         #       zone_id = i["Id"].split("/")[2]
         #       return zone_id 
         #else:
         #    return None

     def list_hosted_zone_by_name(self,domain,MaxItems='1'):
         '''
         传入域名查看域名信息
         '''
         try:
            response = self.client.list_hosted_zones_by_name(DNSName=domain,MaxItems=MaxItems)
         except Exception as e:
             return e.__str__()
         else:
             return response
        
     def list_resource_record_sets(self,host_id):
         '''查看域名解析记录列表
            传入需要查询的域名ID
         '''
         data = {
            'HostedZoneId': host_id,
         }
         records = []
         try:
             def get_records():
                 response = self.client.list_resource_record_sets(**data)
                 records.extend(response['ResourceRecordSets'])
                 if response['IsTruncated']:
                    data['StartRecordName'] = response['NextRecordName']
                    data['StartRecordType'] = response['NextRecordType']
                    get_records()

             get_records()
         except Exception as e:
              return e.__str__()
         else:
             return records
 
     def change_resource_record_sets(self,**kwargs):
         try:
            response = response_content = self.client.change_resource_record_sets(**kwargs)
         except Exception as e:
             return e.__str__()
         else:
             return response
        

# if __name__ == '__main__':
#    start = Aws_api()
#    start.get_hosted_zone()
#    start.get_list_hosted_zones()
#    start.list_hosted_zone_by_name()
#    start.list_resource_record_sets()
