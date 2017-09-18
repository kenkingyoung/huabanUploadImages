# -*- encoding: utf-8 -*-
'''花瓣批量上传图片至指定画板'''
import re
import random
import os
import threading
import imghdr
import requests

class HuabanUploadFiles:
    '''花瓣批量上传图片至指定画板
       email: 用户名
       pwd: 密码
       destination_board_name: 画板名称
       image_dir: 待上传图片存放目录的路径
    '''
    def __init__(self, email, pwd, destination_board_name, image_dir):
        self.email = email
        self.pwd = pwd
        self.destination_board_name = destination_board_name
        self.image_dir = image_dir
        self.session = requests.Session()
        self.headers = {
            'Host':'huaban.com',
            'User-Agent':('Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36')
        }

    def __login(self):
        '''登录花瓣'''
        login_url = 'https://huaban.com/auth/'

        post_data = {
            'email':self.email,
            'password':self.pwd,
            '_ref':'frame'
        }

        html = self.session.post(login_url, headers=self.headers, data=post_data)
        error1_msg = re.findall(r'<div class="text"><i class="error"></i>(.+?)</div>', html.text)
        error2_msg = re.findall(r'app.page\["flash"\] = {"error":\["(.+?)"\]};', html.text)
        if len(error1_msg) > 0 or len(error2_msg) > 0:
            error_msg = ''
            if len(error1_msg) > 0:
                error_msg = error1_msg[0].split('。')[0] + ', 请打开浏览器手动解除登录限制.'
            print('账户登录失败：%s ' % error_msg if error_msg != '' else error2_msg[0])
            print('\n操作已终止。')
            exit()
        else:
            print('用户登录成功。\n')

    def __get_destination_board_id(self):
        '''根据给定画板名获取画板ID'''
        destination_board_id = None

        if len(self.session.cookies) == 0:
            self.__login()

        request_url = ('http://huaban.com/last_boards/?{}&extra=recommend_tags'.
                       format(random.randint(10000000, 99999999)))

        try:
            boards = self.session.get(request_url, headers=self.headers).json()

            for key, value in boards.items():
                for index, item in enumerate(value):
                    if item['title'] == self.destination_board_name:
                        destination_board_id = item['board_id']
                        break

            return destination_board_id
        except Exception as e:
            print('获取画板信息失败: %s ' % e)
            print('\n操作已终止。')
            exit()

    def __get_image_path_list(self):
        '''获取给定目录中所有的图片路径'''
        path_list = []
        if os.path.exists(self.image_dir):
            for dirpath, _, filenames in os.walk(self.image_dir):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if imghdr.what(file_path):
                        path_list.append(file_path)

            return path_list
        else:
            return []

    def __upload_single_image(self, destination_board_id, image_path):
        '''上传图片'''
        file_name = os.path.basename(image_path)

        try:
            image = open(image_path, 'rb')
        except IOError as e:
            print('图片[%s]读取失败：%s ' % (file_name, e))

        files = {
            'file': (file_name, image, 'image/jpeg')
        }
        upload_response = (self.session.post('http://huaban.com/upload/',
                                             files=files, headers=self.headers))

        upload_json = upload_response.json()

        post_data = {
            'board_id': str(destination_board_id),
            'text':file_name,
            'check':'true',
            'file_id':str(upload_json['id']),
            'via':'1',
            'share_button':'0'
        }

        self.session.post('http://huaban.com/pins/', data=post_data, headers=self.headers)
        print('图片[%s]已上传至画板[%s]。' % (file_name, self.destination_board_name))

    def upload(self):
        '''入口方法'''
        if len(self.session.cookies) == 0:
            self.__login()

        destination_board_id = self.__get_destination_board_id()
        if destination_board_id is None:
            print('账户[%s]没有名称为[%s]的画板。' % (self.email, self.destination_board_name))
            print('\n操作已终止。')
            exit()

        image_path_list = self.__get_image_path_list()
        if len(image_path_list) == 0:
            print('该目录[%s]下没有图片文件。' % self.image_dir)
            print('\n操作已终止。')
            exit()

        thread_list = []

        for image_path in image_path_list:
            upload_thread = threading.Thread(target=self.__upload_single_image,
                                             args=(destination_board_id, image_path))
            thread_list.append(upload_thread)
            upload_thread.start()
            print('开始上传图片[%s]...' % os.path.basename(image_path))

        for item in thread_list:
            item.join()

        print('\n图片[共 %s 张]上传已完成。' % len(image_path_list))

if __name__ == '__main__':
    HUABAN = HuabanUploadFiles('kenking0601@163.com', 'kenking0601', '小邋遢',
                               r'D:/PythonCode/huaban_upload_files/img/')
    # HUABAN = HuabanUploadFiles('用户名', '密码', '画板名称', r'存放待上传图片路径')
    HUABAN.upload()
