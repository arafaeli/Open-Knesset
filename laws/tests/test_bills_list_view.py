# encoding: utf-8
#

import unittest
from datetime import date, timedelta, datetime

from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from tagging.models import Tag

from laws.models import Vote, Bill, KnessetProposal, BillBudgetEstimation

from mks.models import Knesset, Member

just_id = lambda x: x.id
APP = 'laws'


class BillListViewsTest(TestCase):
    def setUp(self):
        super(BillListViewsTest, self).setUp()

        d = date.today()
        self.knesset = Knesset.objects.create(
            number=1,
            start_date=d - timedelta(10))
        self.vote_1 = Vote.objects.create(time=datetime.now(),
                                          title='vote 1')
        self.vote_2 = Vote.objects.create(time=datetime.now(),
                                          title='vote 2')
        self.jacob = User.objects.create_user('jacob', 'jacob@example.com',
                                              'JKM')
        self.adrian = User.objects.create_user('adrian', 'adrian@example.com',
                                               'ADRIAN')
        g, created = Group.objects.get_or_create(name='Valid Email')
        ct = ContentType.objects.get_for_model(Tag)
        p = Permission.objects.get(codename='add_tag', content_type=ct)
        g.permissions.add(p)

        self.adrian.groups.add(g)
        self.bill_1 = Bill.objects.create(stage='1', title='bill 1', popular_name="The Bill")
        self.bill_2 = Bill.objects.create(stage='2', title='bill 2')
        self.bill_3 = Bill.objects.create(stage='2', title='bill 1')
        self.kp_1 = KnessetProposal.objects.create(booklet_number=2,
                                                   bill=self.bill_1,
                                                   date=date.today())
        self.mk_1 = Member.objects.create(name='mk 1')
        self.tag_1 = Tag.objects.create(name='tag1')

    def teardown(self):
        super(BillListViewsTest, self).tearDown()

        # self.vote_1.delete()
        # self.vote_2.delete()
        # self.bill_1.delete()
        # self.bill_2.delete()
        # self.bill_3.delete()
        # self.jacob.delete()
        # self.mk_1.delete()
        # self.tag_1.delete()

    def test_bill_list_returns_bills(self):
        res = self.client.get(reverse('bill-list'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'laws/bill_list.html')
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list),
                         [self.bill_3.id, self.bill_2.id, self.bill_1.id])

    def test_bills_are_filtered_by_stage(self):
        res = self.client.get(reverse('bill-list'), {'stage': 'all'})
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list),
                         [self.bill_3.id, self.bill_2.id, self.bill_1.id])
        res = self.client.get(reverse('bill-list'), {'stage': '1'})
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list), [self.bill_1.id])
        res = self.client.get(reverse('bill-list'), {'stage': '2'})
        object_list = res.context['object_list']
        self.assertEqual(set(map(just_id, object_list)), set([self.bill_2.id, self.bill_3.id]))

    def test_bill_list_with_member_returns_only_member_bills(self):
        "Test the view of bills proposed by specific MK"
        res = self.client.get(reverse('bill-list'), {'member': self.mk_1.id})
        self.assertEqual(res.status_code, 200)

    def test_bill_list_with_invalid_member(self):
        "test the view of bills proposed by specific mk, with invalid parameter"
        res = self.client.get(reverse('bill-list'), {'member': 'qwertyuiop'})
        self.assertEqual(res.status_code, 404)

    def test_bill_list_with_nonexisting_member(self):
        "test the view of bills proposed by specific mk, with nonexisting parameter"
        res = self.client.get(reverse('bill-list'), {'member': '0'})
        self.assertEqual(res.status_code, 404)

    def test_bill_list_filtered_by_knesset_booklet(self):
        res = self.client.get(reverse('bill-list'), {'knesset_booklet': '2'})
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list), [self.bill_1.id])

