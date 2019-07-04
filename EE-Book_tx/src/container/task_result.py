# -*- coding: utf-8 -*-
from src.tools.config import Config
from src.tools.db import DB
from src.tools.debug import Debug
from src.tools.match import Match
from src.tools.path import Path
from src.tools.type import Type
from src.container.data.answer import Answer as Answer_Info
from src.container.data.question import Question as Question_Info
from src.container.data.topic import Topic as Topic_Info
from src.container.data.collection import Collection as Collection_Info
from src.container.data.column import Column as Column_Info
from src.container.data.article import Article as Article_Info
from src.container.data.author import Author as Author_Info
from collections import OrderedDict

class Question(object):
    u"""
    问题容器
    """

    def __init__(self, question_info):
        """
        :type question_info : Question_Info
        """
        self.question_info = question_info
        self.answer_list = []  # type: list[Answer_Info]

        self.total_img_size_kb = 0
        self.img_filename_list = []

        self.question_content_img_size = 0
        self.question_content_img_filename_list = []
        return

    def append_answer(self, answer):
        """
        :type answer: Answer_Info
        :return:
        """
        self.answer_list.append(answer)
        return

    def download_img_in_question_content(self):
        #   下载问题详情中的图片，同时更新
        from src.container.image_container import ImageContainer
        img_container = ImageContainer()
        img_src_dict = Match.match_img_with_src_dict(self.question_info.detail)
        self.question_content_img_filename_list = []
        for img in img_src_dict:
            src = img_src_dict[img]
            filename = img_container.add(src)
            self.question_content_img_filename_list.append(filename)
            self.question_info.detail = self.question_info.detail.replace(img, Match.create_img_element_with_file_name(filename))

        img_container.start_download()

        #   下载完成后，更新图片大小
        for filename in self.question_content_img_filename_list:
            self.question_content_img_size += Path.get_img_size_by_filename_kb(filename)
        return

    def download_img(self):
        #   下载图片，同时更新
        Debug.logger.debug(u'开始下载问题{}内问题详情中的图片'.format(self.question_info.question_id))
        self.download_img_in_question_content()
        Debug.logger.debug(u'开始下载问题{}内答案中的图片'.format(self.question_info.question_id))
        index = 1
        for answer in self.answer_list:
            Debug.logger.debug(u'开始下载问题{}中第{}个答案的图片'.format(self.question_info.question_id, index))
            answer.download_img()
            self.total_img_size_kb += answer.total_img_size_kb
            index += 1

        #   忘了更新问题内的图片名列表了= =
        self.update_img_filename_list_in_answer()
        Debug.logger.debug(u'问题{}内答案中的图片全部下载完成'.format(self.question_info.question_id))

        return

    def compute_total_img_size_kb(self):
        self.total_img_size_kb = self.question_content_img_size
        for answer in self.answer_list:
            self.total_img_size_kb += answer.total_img_size_kb
        return self.total_img_size_kb

    def update_img_filename_list_in_answer(self):
        self.img_filename_list = []
        for answer in self.answer_list:
            self.img_filename_list += answer.img_filename_list
        #   加上问题中本身的图片地址
        self.img_filename_list += self.question_content_img_filename_list
        return

    def auto_split(self, max_size_page_kb):
        legal_question = Question(self.question_info)
        remain_question = Question(self.question_info)
        while len(self.answer_list) > 1 and self.compute_total_img_size_kb() > max_size_page_kb:
            answer = self.answer_list.pop()
            remain_question.answer_list.insert(0, answer)

        #   更新自有属性
        legal_question.question_content_img_filename_list = self.question_content_img_filename_list
        legal_question.question_content_img_size = self.question_content_img_size

        # 最后再更新一下图片大小
        legal_question.compute_total_img_size_kb()
        remain_question.compute_total_img_size_kb()
        # 更新图片文件名列表
        legal_question.update_img_filename_list_in_answer()
        remain_question.update_img_filename_list_in_answer()
        return legal_question, remain_question


class Column(object):
    u"""
    专栏容器
    """

    def __init__(self, column_info):
        """
        :type column_info : Column_Info
        """
        self.column_info = column_info
        self.article_list = [] # type: list[Article_Info]

        self.total_img_size_kb = 0
        self.img_filename_list = []
        return

    def append_article(self, article):
        """
        :type article: Article_Info
        """
        self.article_list.append(article)
        return

    def download_img(self):
        #   下载图片，同时更新
        Debug.logger.debug(u'开始下载专栏{}内文章中的图片'.format(self.column_info.column_id))
        index = 1
        for article in self.article_list:
            Debug.logger.debug(u'开始下载专栏{}中第{}篇文章的图片'.format(self.column_info.column_id, index))
            article.download_img()
            self.total_img_size_kb += article.total_img_size_kb
            print u'total_img_size_kb : {}'.format(self.total_img_size_kb)
            index += 1
        Debug.logger.debug(u'专栏{}内文章中的图片全部下载完成'.format(self.column_info.column_id))
        self.update_img_filename_list_in_article()
        return

    def update_img_filename_list_in_article(self):
        self.img_filename_list = []
        for article in self.article_list:
            self.img_filename_list += article.img_filename_list
        return


class TaskResult(object):
    u"""
    收集任务执行的结果
    """

    def __init__(self, task):
        u"""
        :type task src.container.task.AnswerTask | src.container.task.QuestionTask | src.container.task.TopicTask| src.container.task.CollectionTask | src.container.task.AuthorTask | src.container.task.ColumnTask | src.container.task.ArticleTask
        """
        self.task = task

        self.question_list = []  # type: list[Question]
        self.column_list = []   # type: list[Column]
        self.info_page = None  # type:  Answer_Info|Question_Info|Topic_Info|Collection_Info|Column_Info|Article_Info|Author_Info

        self.is_split = False  # 是否是被拆分后的结果集
        self.chapter_no = 0  # 若是被拆分后的结果集，那么是哪一集
        return

    def download_img(self):
        #   下载图片
        Debug.logger.debug(u'开始下载问题列表中的图片')
        index = 1
        for question in self.question_list:
            Debug.logger.debug(u'开始下载问题列表中第{}个问题的图片'.format(index))
            question.download_img()
        Debug.logger.debug(u'开始下载专栏中的图片')
        index = 1
        for column in self.column_list:
            Debug.logger.debug(u'开始下载专栏列表中第{}篇专栏的图片'.format(index))
            column.download_img()
        Debug.logger.debug(u'恭喜，图片全部下载完成')
        return

    def auto_split(self, max_size_page_kb):
        if max_size_page_kb < 1 * 1024:
            #   不能任意小啊
            max_size_page_kb = 1 * 1024
        if self.get_total_img_size_kb() <= max_size_page_kb:
            #   大小符合要求，最好
            remain_task_result = TaskResult(self.task)
            remain_task_result.info_page = self.info_page
            remain_task_result.is_split = True
            remain_task_result.chapter_no = self.chapter_no + 1
            return self, remain_task_result

        if not self.is_split:
            # 第一次分隔，序号应该为卷1
            self.is_split = True
            self.chapter_no = 1

        if self.task.task_type == Type.column or self.task.task_type == Type.article:
            #   文章和问题分别对待，方便处理
            remain_task_result = TaskResult(self.task)
            remain_task_result.info_page = self.info_page
            remain_task_result.is_split = True
            remain_task_result.chapter_no = self.chapter_no + 1
            while len(self.column_list) > 1 and self.get_total_img_size_kb() > max_size_page_kb:
                column = self.column_list.pop()
                remain_task_result.column_list.insert(0, column)
            return self, remain_task_result
        else:
            #   文章和问题分别对待，方便处理
            remain_task_result = TaskResult(self.task)
            remain_task_result.info_page = self.info_page
            remain_task_result.is_split = True
            remain_task_result.chapter_no = self.chapter_no + 1

            while self.get_total_img_size_kb() > max_size_page_kb:
                question = self.question_list.pop()
                if len(self.question_list) == 0:
                    # 最后一个问题
                    legal_question, remain_question = question.auto_split(max_size_page_kb)
                    self.question_list.append(legal_question)
                    remain_task_result.question_list.insert(0, remain_question)
                    return self, remain_task_result
                else:
                    remain_task_result.question_list.insert(0, question)
            return self, remain_task_result

    def get_total_img_size_kb(self):
        total_img_size_kb = 0
        for question in self.question_list:
            total_img_size_kb += question.total_img_size_kb
        for column in self.column_list:
            total_img_size_kb += column.total_img_size_kb
        return total_img_size_kb

    def get_title(self):
        """
        获取任务对应的标题
        :rtype: str
        """
        if self.task.task_type == Type.question:
            return u'知乎问题({question_id})答案集'.format(question_id=self.task.question_id)
        elif self.task.task_type == Type.answer:
            return u'知乎回答({answer_id})'.format(answer_id=self.task.answer_id)
        elif self.task.task_type == Type.author:
            return u'知乎作者{name}({author_page_id})答案集'.format(name=self.info_page.name, author_page_id=self.task.author_page_id)
        elif self.task.task_type == Type.topic:
            return u'知乎话题{name}({topic_id})答案集'.format(name=self.info_page.name, topic_id=self.task.topic_id)
        elif self.task.task_type == Type.collection:
            return u'知乎收藏夹{name}({collection_id})答案集'.format(name=self.info_page.title, collection_id=self.task.collection_id)
        elif self.task.task_type == Type.column:
            if self.info_page.title == self.task.column_id:
                return u'({name})文章集'.format(name=self.info_page.title)
            else:
                # return u'专栏{name}({column_id})文章集'.format(name=self.info_page.title, column_id=self.task.column_id)
                return u'{name}'.format(name=self.info_page.title, column_id=self.task.column_id)
                # return u'{name}({column_id})'.format(name=self.info_page.title, column_id=self.task.column_id)
        elif self.task.task_type == Type.article:
            return u'知乎文章({article_id})'.format(article_id=self.task.article_id)
        elif self.task.task_type == Type.huxiu:
            return u'虎嗅({article_id})'.format(article_id=self.task.account_id)
        return

    def extract_data(self):
        u"""
        根据task类型，从数据库中抽取数据
        :return:
        """
        if self.task.task_type == Type.question:
            self.extract_question()
        elif self.task.task_type == Type.answer:
            self.extract_answer()
        elif self.task.task_type == Type.author:
            self.extract_author()
        elif self.task.task_type == Type.topic:
            self.extract_topic()
        elif self.task.task_type == Type.collection:
            self.extract_collection()
        elif self.task.task_type == Type.column:
            self.extract_column()
        elif self.task.task_type == Type.article:
            self.extract_article()
        return

    def extract_question(self):
        self.info_page = self.query_question(self.task.question_id)
        question = Question(self.info_page)
        answer_list = self.query_answer_list_by_question_id(self.task.question_id)
        for answer in answer_list:
            question.append_answer(answer)
        self.question_list.append(question)
        return

    def extract_answer(self):
        """
        和question一样，只是只取一个answer
        :return:
        """
        self.info_page = self.query_question(self.task.question_id)
        question = Question(self.info_page)
        answer = self.query_answer(self.task.answer_id)
        question.append_answer(answer)
        self.question_list.append(question)
        return

    def extract_topic(self):
        raw_topic = DB.query_row(u'select * from Topic where topic_id="{topic_id}"'.format(topic_id=self.task.topic_id))
        self.info_page = Topic_Info(raw_topic)

        answer_list = self.query_answer_list(self.info_page.best_answer_id_list.split(','))
        question_id_dict = OrderedDict()
        #   依次获取对应的Question对象
        for answer in answer_list:
            if answer.question_id not in question_id_dict:
                question_id_dict[answer.question_id] = Question(self.query_question(answer.question_id))
            question_id_dict[answer.question_id].append_answer(answer)
        for question_id in question_id_dict:
            self.question_list.append(question_id_dict[question_id])
        return

    def extract_collection(self):
        raw_collection = DB.query_row(
                u'select * from Collection where collection_id="{collection_id}"'.format(collection_id=self.task.collection_id))
        self.info_page = Collection_Info(raw_collection)

        answer_list = self.query_answer_list(self.info_page.collected_answer_id_list.split(','))
        question_id_dict = OrderedDict()
        #   依次获取对应的Question对象
        for answer in answer_list:
            if answer.question_id not in question_id_dict:
                question_id_dict[answer.question_id] = Question(self.query_question(answer.question_id))
            question_id_dict[answer.question_id].append_answer(answer)
        for question_id in question_id_dict:
            self.question_list.append(question_id_dict[question_id])
        return

    def extract_author(self):
        raw_author = DB.query_row(u'select * from Author where author_page_id="{author_page_id}" '.format(author_page_id=self.task.author_page_id))
        self.info_page = Author_Info(raw_author)

        answer_list = self.query_answer_list_by_author_page_id(self.info_page.author_page_id)
        question_id_dict = OrderedDict()
        #   依次获取对应的Question对象
        for answer in answer_list:
            if answer.question_id not in question_id_dict:
                db_question_info = self.query_question(answer.question_id)
                if not db_question_info:
                    #   当返回值为空的时候，直接跳过即可
                    continue
                question_id_dict[answer.question_id] = Question(db_question_info)
            question_id_dict[answer.question_id].append_answer(answer)
        for question_id in question_id_dict:
            self.question_list.append(question_id_dict[question_id])
        return

    def extract_column(self):
        self.info_page = self.query_column(self.task.column_id)
        column = Column(self.info_page)
        article_list = self.query_article_list_by_column_id(self.task.column_id)
        for article in article_list:
            column.append_article(article)
        self.column_list.append(column)
        return

    def extract_article(self):
        self.info_page = self.query_column(self.task.column_id)
        column = Column(self.info_page)
        article = self.query_article(self.task.article_id)
        column.append_article(article)
        self.column_list.append(column)
        return

    def query_question(self, question_id):
        """
        :rtype: Question_Info
        """
        question = DB.query_row(u'select * from Question where question_id in ({question_id})'.format(question_id=question_id))
        question = self.format_question(question)  # 包装成标准的信息格式
        return question

    def query_question_list(self, question_id_list):
        raw_question_list = DB.query_all(
                u'select * from Question where question_id in ({question_id_list})'.format(question_id_list=','.join(question_id_list)))
        question_list = []
        for raw_question in raw_question_list:
            question_list.append(self.format_question(raw_question))
        return question_list

    def query_answer(self, answer_id):
        """

        :type answer_id:int
        :return:
        """
        answer = DB.query_row(u'select * from Answer where answer_id in ({answer_id})'.format(answer_id=answer_id))
        answer = self.format_answer(answer)
        return answer

    def query_answer_list(self, answer_id_list):
        raw_answer_list = DB.query_all(u'select * from Answer where answer_id in ({answer_id_list}) {order_by} '.format(answer_id_list=','.join(answer_id_list), order_by=Config.topic_or_collection_answer_order_by))
        answer_list = []
        for raw_answer in raw_answer_list:
            answer_list.append(self.format_answer(raw_answer))
        return answer_list

    def query_answer_list_by_author_page_id(self, author_page_id):
        # 需要先查出来对应的author_id
        author_info = DB.query_row(u'select author_id from Author where author_page_id="{author_page_id}"'.format(author_page_id=author_page_id))
        author_id = author_info[u'author_id']
        raw_answer_list = DB.query_all(u'select * from Answer where author_id="{author_id}"  {order_by} '.format(author_id=author_id, order_by=Config.answer_order_by))
        answer_list = []
        for raw_answer in raw_answer_list:
            answer_list.append(self.format_answer(raw_answer))
        return answer_list

    def query_answer_list_by_question_id(self, question_id):
        raw_answer_list = DB.query_all(
                u'select * from Answer where question_id="{question_id}" {order_by} '.format(question_id=question_id, order_by=Config.answer_order_by))
        answer_list = []
        for raw_answer in raw_answer_list:
            answer_list.append(self.format_answer(raw_answer))
        return answer_list

    def format_answer(self, raw_answer):
        """
        :rtype: Answer_Info
        """
        return Answer_Info(raw_answer)

    def format_question(self, raw_question):
        """
        :rtype: Question_Info
        """
        return Question_Info(raw_question)

    def query_column(self, column_id):
        raw_column = DB.query_row(u'select * from Column where column_id="{column_id}"'.format(column_id=column_id))
        column = self.format_column(raw_column)  # 包装成标准的信息格式
        return column

    def query_article(self, article_id):
        print u"query_article {}".format(article_id)
        raw_article = DB.query_row(u'select * from Article where article_id="{article_id}" '.format(article_id=article_id))
        article = self.format_article(raw_article)
        return article

    def query_article_list_by_column_id(self, column_id):
        #   根据发表时间正序获取文章列表，方便浏览
        print u'select * from Article where column_id = "{column_id}"    {order_by}'.format(column_id=column_id,  order_by=Config.article_order_by)
        raw_article_list = DB.query_all(u'select * from Article where column_id = "{column_id}"    {order_by}'.format(column_id=column_id,  order_by=Config.article_order_by))
        article_list = []
        for raw_article in raw_article_list:
            article = self.format_article(raw_article)
            article_list.append(article)
        return article_list

    def format_article(self, raw_article):
        """
        :rtype: Article_Info
        """
        return Article_Info(raw_article)

    def format_column(self, raw_column):
        """
        :rtype: Column_Info
        """
        return Column_Info(raw_column)
