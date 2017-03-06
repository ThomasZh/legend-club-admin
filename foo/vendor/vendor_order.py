#!/usr/bin/env python
# _*_ coding: utf-8_*_
#
# Copyright 2016 planc2c.com
# dev@tripc2c.com
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import tornado.web
import logging
import uuid
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../dao"))

from tornado.escape import json_encode, json_decode
from tornado.httpclient import HTTPClient
from tornado.httputil import url_concat

from comm import BaseHandler
from comm import timestamp_datetime
from comm import datetime_timestamp
from comm import timestamp_date
from comm import date_timestamp

from dao import budge_num_dao
from dao import category_dao
from dao import activity_dao
from dao import group_qrcode_dao
from dao import cret_template_dao
from dao import bonus_template_dao
from dao import apply_dao
from dao import order_dao
from dao import group_qrcode_dao
from dao import insurance_template_dao
from dao import vendor_member_dao
from dao import voucher_order_dao

from global_const import VENDOR_ID
from global_const import STP
from global_const import PAGE_SIZE_LIMIT


class VendorOrderListHandler(BaseHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        session_ticket = self.get_session_ticket()
        my_account = self.get_account_info()

        before = time.time()
        _array = order_dao.order_dao().query_pagination_by_vendor(vendor_id, before, PAGE_SIZE_LIMIT);
        for order in _array:
            _activity = activity_dao.activity_dao().query(order['activity_id'])
            order['activity_title'] = _activity['title']

            try:
                order['base_fees']
            except:
                order['base_fees'] = _activity['base_fee_template']
                # 数据库apply无base_fees时，取order的赋值给它，并更新其数据库字段
                _json = {"_id":order['_id'],"base_fees":order['base_fees']}
                logging.info("got base_fees json %r in uri", _json)
                order_dao.order_dao().update(_json)

            order['activity_amount'] = 0
            if order['base_fees']:
                for base_fee in order['base_fees']:
                    # 价格转换成元
                    order['activity_amount'] = float(base_fee['fee']) / 100

            order_fees = []
            for ext_fee_id in order['ext_fees']:
                for template in _activity['ext_fee_template']:
                    if ext_fee_id == template['_id']:
                        json = {"_id":ext_fee_id, "name":template['name'], "fee":template['fee']}
                        order_fees.append(json)
                        break
            order['fees'] = order_fees

            order_insurances = []
            for insurance_id in order['insurances']:
                _insurance = insurance_template_dao.insurance_template_dao().query(insurance_id)
                order_insurances.append(_insurance)
            order['insurances'] = order_insurances

            for _voucher in order['vouchers']:
                # 价格转换成元
                _voucher['fee'] = float(_voucher['fee']) / 100

            try:
                order['bonus']
            except:
                order['bonus'] = 0
            # 价格转换成元
            order['bonus'] = float(order['bonus']) / 100
            try:
                order['payed_total_fee'] = float(order['payed_total_fee']) / 100
            except:
                order['payed_total_fee'] = 0

        budge_num = budge_num_dao.budge_num_dao().query(vendor_id)
        self.render('vendor/orders.html',
                vendor_id=vendor_id,
                my_account=my_account,
                budge_num=budge_num,
                orders=_array)


class VendorApplyListHandler(BaseHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        session_ticket = self.get_session_ticket()
        my_account = self.get_account_info()

        before = time.time()
        _array = apply_dao.apply_dao().query_pagination_by_vendor(vendor_id, before, PAGE_SIZE_LIMIT);
        for _apply in _array:
            activity = activity_dao.activity_dao().query(_apply['activity_id'])
            _apply['activity_title'] = activity['title']
            _apply['create_time'] = timestamp_datetime(_apply['create_time'])
            if _apply['gender'] == 'male':
                _apply['gender'] = u'男'
            else:
                _apply['gender'] = u'女'
            try:
                _apply['note']
            except:
                _apply['note'] = ''

        budge_num = budge_num_dao.budge_num_dao().query(vendor_id)
        self.render('vendor/applys.html',
                vendor_id=vendor_id,
                my_account=my_account,
                budge_num=budge_num,
                applys=_array)


class VendorVoucherOrderListHandler(BaseHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id):
        logging.info("got vendor_id %r in uri", vendor_id)

        session_ticket = self.get_session_ticket()
        my_account = self.get_account_info()

        before = time.time()
        _array = voucher_order_dao.voucher_order_dao().query_pagination_by_vendor(vendor_id, before, PAGE_SIZE_LIMIT);
        for _voucher_order in _array:
            _voucher_order['voucher_price'] = float(_voucher_order['voucher_price'])/100
            _voucher_order['voucher_amount'] = float(_voucher_order['voucher_amount'])/100
            _voucher_order['create_time'] = timestamp_datetime(_voucher_order['create_time'])

        budge_num = budge_num_dao.budge_num_dao().query(vendor_id)
        self.render('vendor/voucher-orders.html',
                vendor_id=vendor_id,
                my_account=my_account,
                budge_num=budge_num,
                voucher_orders= _array)


class VendorOrderInfoHandler(BaseHandler):
    @tornado.web.authenticated  # if no session, redirect to login page
    def get(self, vendor_id, order_id):
        logging.info("got vendor_id %r in uri", vendor_id)
        logging.info("got order_id %r in uri", order_id)

        _session_ticket = self.get_session_ticket()
        my_account = self.get_account_info()

        order = order_dao.order_dao().query(order_id)
        _activity = activity_dao.activity_dao().query(order['activity_id'])
        order['activity_title'] = _activity['title']

        if not order['base_fees']:
            order['activity_amount'] = 0
        else:
            for base_fee in order['base_fees']:
                # 价格转换成元
                order['activity_amount'] = float(base_fee['fee']) / 100

        order['create_time'] = timestamp_datetime(order['create_time'])

        customer_profile = vendor_member_dao.vendor_member_dao().query_not_safe(vendor_id, order['account_id'])
        order['account_nickname'] = customer_profile['account_nickname']
        order['account_avatar'] = customer_profile['account_avatar']
        try:
            order['prepay_id']
        except:
            order['prepay_id'] = ''
        try:
            order['transaction_id']
        except:
            order['transaction_id'] = ''
        try:
            order['payed_total_fee']
        except:
            order['payed_total_fee'] = 0

        for _voucher in order['vouchers']:
            # 价格转换成元
            _voucher['fee'] = float(_voucher['fee']) / 100

        _applys = apply_dao.apply_dao().query_by_order(order_id)
        for _apply in _applys:
            _apply['activity_title'] = _activity['title']
            logging.info("got activity_title %r", _apply['activity_title'])
            _apply['create_time'] = timestamp_datetime(_apply['create_time'])
            if _apply['gender'] == 'male':
                _apply['gender'] = u'男'
            else:
                _apply['gender'] = u'女'

            _apply['account_nickname'] = customer_profile['account_nickname']
            _apply['account_avatar'] = customer_profile['account_avatar']
            try:
                _apply['note']
            except:
                _apply['note'] = ''

        for ext_fee in order['ext_fees']:
            # 价格转换成元
            ext_fee['fee'] = float(ext_fee['fee']) / 100

        for insurance in order['insurances']:
            # 价格转换成元
            insurance['fee'] = float(insurance['fee']) / 100

        # order['activity_amount'] = float(_activity['amount']) / 100
        if not order['base_fees']:
            order['activity_amount'] = 0
        else:
            for base_fee in order['base_fees']:
                # 价格转换成元
                order['activity_amount'] = float(base_fee['fee']) / 100

        order['total_amount'] = float(order['total_amount']) / 100
        order['bonus'] = float(order['bonus']) / 100
        order['payed_total_fee'] = float(order['payed_total_fee']) / 100

        budge_num = budge_num_dao.budge_num_dao().query(vendor_id)
        self.render('vendor/order-detail.html',
                vendor_id=vendor_id,
                my_account=my_account,
                budge_num=budge_num,
                activity=_activity, order=order, applys=_applys)
