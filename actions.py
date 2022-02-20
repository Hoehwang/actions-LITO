# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

import pandas as pd
import random
import numpy as np
import re
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

res = pd.read_csv("./actions/RESPONSE_EXP_LITO.csv", encoding = 'utf8')
syn = pd.read_csv("./actions/SYN.csv", encoding = 'utf8')
ac_ta = pd.read_csv('./actions/LITO_ACTION_TABLE.csv', encoding = 'utf8') # 질병별 증상 정보에 대한 mapping table

class ActionRephraseResponse(Action):
        
    # 액션에 대한 이름을 설정
    def name(self) -> Text:
        return "action_rephrase_stock"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(tracker.latest_message['entities'])
        print(tracker.get_intent_of_latest_message())
        
        
        self.intent = tracker.get_intent_of_latest_message()
        self.entity = tracker.latest_message['entities'][0]['entity']
        if self.entity != 'STOCK':
            self.entity_norm = syn[syn["entity"]==self.entity]["norm"].item()
        else: 
            temp_entity = tracker.latest_message['entities'][0]['value']
            self.entity_norm = syn[syn['norm'].str.contains(temp_entity.upper())]["norm"].values[0]
            self.entity = self.entity_norm
            print(self.entity, self.entity_norm)

        self.article_exist = True
        pol_mapper = {'pos':'[긍정]', 'neg':'[부정]', 'neu':'[중립]'}
        num_mapper = {1:'첫', 2:'두', 3:'세'}
        sort_key = ['date']
        ac_ta_sorted_by_values = ac_ta.sort_values(by=sort_key ,ascending=False)
        res_df = ac_ta_sorted_by_values[ac_ta_sorted_by_values['ent']==self.entity]
        if res_df.size == 0:
            res_df = ac_ta_sorted_by_values[ac_ta_sorted_by_values['stock']==self.entity]

        if self.intent == 'INFO-GOOD_STOCK':
            res_df = res_df[res_df['polarity']=='pos']
        elif self.intent == 'INFO-BAD_STOCK':
            res_df = res_df[res_df['polarity']=='neg']
        else:
            res_df = res_df[(res_df['polarity']=='pos') | (res_df['polarity']=='neg')]
        
        if res_df.size == 0:
            self.article_exist = False
        elif res_df.size < 3:
            output_data_ls = list(zip(res_df['date_str'].to_list(), res_df['title'].to_list(), res_df['link'].to_list(), res_df['polarity'].to_list()))
        else:
            output_data_ls = list(zip(res_df['date_str'].to_list()[:3], res_df['title'].to_list()[:3], res_df['link'].to_list()[:3], res_df['polarity'].to_list()[:3]))

        nlg_form = random.choice(res[res["intent"]==self.intent]["response"].values[0].split(' / '))
        nlg_form = nlg_form.replace('<STOCK_FEATURE>',self.entity_norm)

        
        dispatcher.utter_message(text=nlg_form)

        if self.article_exist:
            dispatcher.utter_message(text=res[res["intent"]==self.intent]["send_before"].item())
            dispatcher.utter_message(text=random.choice(res[res["intent"]==self.intent]["send_link"].item().split(' / ')))
            
            for i, o in enumerate(output_data_ls):
                if i > 2: break

                # dispatcher.utter_message(text='{num}) {date}, {pol}, {title}'.format(num=i+1, date=o[0], pol=pol_mapper[o[3]], title=o[1]))
                show_article_data_form = res[res["intent"]==self.intent][o[3]].values[0]
                show_article_data_form = show_article_data_form.replace('<STOCK_FEATURE>',self.entity_norm)
                show_article_data_form = show_article_data_form.replace('<NUM_FEATURE>',num_mapper[i+1])

                dispatcher.utter_message(text = show_article_data_form)
                dispatcher.utter_message(text = '날짜: ' + o[0] + '\n' +'제목글: '  + o[1])
                dispatcher.utter_message(text=o[2])

            dispatcher.utter_message(text=res[res["intent"]==self.intent]["utter_ask_more"].item())
        else:
            dispatcher.utter_message(text=res[res["intent"]==self.intent]["entityless"].item())



#들어온 인텐트, 엔티티에 대해 다음과 같이 처리
#syn에서 엔티티 대표값 가져오기, 
#entity값으로 ac_ta 조건 추출 후, 시간 순으로 정렬 상위 3개 추출(혹은 시간 순 정렬 후, entity값 상위 3개 추출)
#추출한 ac_ta에서 날짜, 기사글, 링크, 긍/부정 정보 가져오기
#res에서 답변 출력하기
 