#coding:utf-8
#author:胖胖小飞侠
import os
import re
import csv
import urllib.parse
import dns.resolver
import requests
from lxml import etree
from prettytable import PrettyTable#以表格形式显示
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import ReadTimeout,HTTPError,RequestException
obj1 = re.compile(r'charset=[\S]*?([a-zA-Z0-9_-]*)\S',re.S|re.I)
obj2 = re.compile(r'<title>(?P<title>).*?</title>',re.S|re.I)
headers = {
"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
}
def getYm():
    f = 'url.txt'
    url = []
    with open(f,'r',encoding='utf-8') as fp:#读取文件信息
        for line in fp:
            line = line.strip('\n').replace(" ","")
            if line not in url:
                url.append(line)
    return url
url = getYm()
def getDnsA(i):#返回DNS解析
    cf_i = urllib.parse.urlparse(i)
    netloc = cf_i.netloc
    netloc = netloc.split(':')[0]
    domain = netloc
    # print(netloc)
    al = ''
    try:
        A = dns.resolver.resolve(domain,"A")
        for a in A.response.answer:
            alist = []
            for aa in a.items:
                if aa.address not in alist:
                    alist.append(aa.address)
            al = '\t'.join(alist)
            # print("{:30}\t\tDNS解析地址：\t{}".format(domain,al))
        return al
    except:
        print('未正确解析'+domain)
def get_title(z):
    # print("正在检查：{}".format(z))
    encode = ''#设置默认值
    encode1 = ''
    encode2 = ''
    exists_length = False#设置默认值
    length = 0
    code = '---'
    server = '未知'#中间件
    title = '===未知标题==='
    try:
        resp = requests.get(z,headers=headers,timeout=10)
        code = resp.status_code#响应码
        resp_headers = resp.headers
        exists_length = 'Content-Length' in resp_headers.keys()
        if exists_length == True:
            chang = resp_headers.get('Content-Length')
            length = chang
        else:
            length = 0
        server = resp_headers['Server']
        if server != '******':
            server = server
        if resp.status_code == 200:
            if resp.text != '':
                encode1 = resp.apparent_encoding
                encode2 = resp.encoding
                # print(encode1,encode2)
                if encode1 == 'UTF-8-SIG':
                    encode = 'utf-8'
                if encode2 != 'ISO-8859-1' and encode2 != '':
                    encode = encode2
                if encode1 == 'ascii' or encode2 == 'ISO-8859-1':
                    html =etree.HTML(resp.text)
                    charset_x = html.xpath('//meta/@charset')#获取meta节点下的charset属性
                    if charset_x != []:
                        # print(encode+'ffffffffffffffffffff')
                        encode = charset_x[0]
                    if charset_x == []:
                        try:
                            result1 = obj1.search(resp.text)
                            encode = result1.group(1).strip('"').strip("'").strip('\\')
                        except AttributeError:
                            print(z+"\t编码匹配错误！")
                        except Exception as e:
                            print(z+"\t出错原因1：",e)
                if encode == '':#无能为力，只能盲猜GBK
                    if 'utf-8' in resp.text or 'UTF-8' in resp.text:
                        encode ='utf-8'
                    if 'gbk' in resp.text or 'GBK' in resp.text or 'gb2312' in resp.text or 'GB2312' in resp.text:
                        encode = 'gbk'
                    if encode == '':
                        encode = 'utf-8'
            resp.encoding = encode
            resp.close()
            try:
                new_resp_text = resp.text.replace(" ","")#去除空格
                result2 =obj2.search(new_resp_text)
                title = result2.group(0).strip()
                #对可能存在html编码的进行转码，不需要判断，有就转，没有就不转
                import html
                title = html.unescape(title)
                title = "".join(title.split()).replace("<title>","").replace("</title>","").replace("<TITLE>","").replace("</TITLE>","")
                # print(title)
            except AttributeError:
                print(z+"\t匹配错误ab！")
            except Exception as e:
                print(z+"\t出错原因2：",e)
    except ReadTimeout:
        print(z+'\t异常:ReadTimeout')
    except HTTPError:
        print(z+'\t异常:HTTPError')
    except RequestException:
        print(z+'\t异常:RequestException')
    
    # z,code,server,length
    return [z,title,code,server,length,encode,encode1,encode2]
pool = ThreadPoolExecutor(30)#创建线程资源池
u = PrettyTable(['地址','标题','响应码','中间件','编码','编码1','编码2','长度','DNS解析地址'])
u.align['地址','标题']='l'#左对齐
u._max_width = {'地址':35,'标题':45,'响应码':10,'中间件':15,'编码1':10,'长度':10,'DNS解析地址':25}
# # 
def main(i):   
    if get_title(i) != None:
        gd = getDnsA(i)
        ulist = list(get_title(i))
        # print(type(ulist))
        ulist.append(gd)
        u.add_row(ulist)
    else:
        badurl = [i,'===未知标题===','---','******','---','---','---','---','---']
        u.add_row(badurl)
for i in url:
    pool.submit(main,i)
pool.shutdown(True)  
print(u.get_string())
html = u.get_html_string()#输出为html
# print(html)
with open('test.html','w',encoding='utf-8') as hp:
    hp.write(html)