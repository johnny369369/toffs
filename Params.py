import sys,os
class Params():
    colour_list = {
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'purple_red': 35,
        'bluish_blue': 36,
        'white': 37,
    }

    def __init__(self):
        pass

    @staticmethod
    def display(msg, colour='white'):
        choice = Params.colour_list.get(colour)
        if choice:
            info = "\033[1;{};1m{}\033[0m".format(choice, msg)
            return info
        else:
            return False

    @staticmethod
    def check_input(msg, result=[]):
        '''获取用户输入
        返回选择或退出'''

        def entry(msg):
            ret = input('请输入{},或输入q退出: '.format(msg)).strip()
            return ret

        choice = entry(msg)
        result.append(choice)
        if not choice:
            check_input(msg)
        else:
            if choice == 'q':
                sys.exit(0)
        return result[-1]

    @staticmethod
    def check_menu_dict(data, title):
        '''菜单字典
           返回用户选择操作'''
        try:
            user_input = ''
            while user_input.strip() not in data:
                for key in data:
                    print('\t', key, data[key])
                user_input = input(f'请选择{title},或输入q退出:').strip()
                if user_input == 'q':
                    sys.exit(1)
            return user_input.strip()
        except Exception as e:
            print(e)
