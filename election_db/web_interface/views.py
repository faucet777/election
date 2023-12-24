import json

from django.http import HttpRequest
from django.shortcuts import render
from .forms import *
from collections import Counter
import plotly
import plotly.graph_objects as go
import db_connector


cl = db_connector.pymongo.MongoClient()
menu_data = db_connector.get_collections_tree(cl)
db0, col0 = list(menu_data.items())[0][0], list(menu_data.items())[0][1][2]
cllctn_default = cl[db0][col0]
preview_default = list(cllctn_default.find(limit=100))





def base_page(request):
    return render(request, 'base.html',{'menu_data': menu_data})

def base_group(request):
    # print(menu_data)
    return render(request, 'base_grouping.html',{'menu_data': menu_data})


def content_section(request, group_name, item_name):
    cur = db_connector.connect_mongodb(group_name, item_name).find(limit=100)
    preview = list(cur)
    search_form = Searches()
    if request.method == 'POST':
        print('1st if request.post>>>>', request.POST)
        search_form = Searches(request.POST)
        print('after 1st if is valid?>>>>>>>', search_form.is_valid())
        if search_form.is_valid():
            print('2nd if search_form.cleaned data>>>>', search_form.cleaned_data)
            search_form = Searches(search_form.cleaned_data)
            cur = db_connector.connect_mongodb(group_name, item_name).find(db_connector.make_find_query(request))
            preview = list(cur)
            print(preview)
            print('after 2nd if is valid?>>>', search_form.is_valid())

    print('before render form.data', search_form.data)
    print('before render is valid?>>>>>', search_form.is_valid())
    return render(request, 'content_section.html', {'group_name': group_name,
                                                 'item_name': item_name,
                                                 'sform': search_form,
                                                 'menu_data': menu_data,
                                                 'preview_data': preview})


def group_section(request:HttpRequest, group_name, item_name):
    preview = db_connector.group_by_family(cl[group_name][item_name])
    search_form = Searches()
    if request.method == 'GET':
        try:
            qry = db_connector.make_find_query(request)
            preview = db_connector.group_by_family_find(cl[group_name][item_name],qry)
            print('GET search grouping>>>>',preview)
        except:
            preview = db_connector.group_by_family(cl[group_name][item_name])
    if request.method == 'POST':
        search_form = Searches(request.POST)
        if search_form.is_valid():
            print('2nd if search_form.cleaned data>>>>', search_form.cleaned_data)
            citizID = request.POST['_id']
            print('citiz ID>>>>>>>', citizID)
            collctn = db_connector.connect_mongodb(group_name, item_name)
            db_connector.change_citizen(collctn, citizID, search_form.cleaned_data)
        preview = db_connector.group_by_family(cl[group_name][item_name])

    fams_list = []
    for fam in preview:
        [(head, membs)] = fam.items()
        mforms = []
        for memb in membs:
            mforms.append(Member(memb))

        fam_dict = {
            head: mforms,
        }
        fams_list.append(fam_dict)
    pie = db_connector.get_svg_data(db_connector.connect_mongodb(group_name, item_name))
    return render(request, 'group_section.html', {'group_name': group_name,
                                                 'item_name': item_name,
                                                 'sform': search_form,
                                                 'menu_data': menu_data,
                                                 'group_data': fams_list,
                                                 'pie_data': pie,})


def pie_chart_view(request):
    # Sample data (Replace this with your actual data)
    data = preview_default

    # Extract properties for plotting
    age_groups = [item['age_group'] for item in data]
    parties = [item['grouping'] for item in data]
    genders = [item['gender'] for item in data]

    # Create pie charts for each property
    age_group_counts = dict(Counter(age_groups))
    age_group_fig = go.Figure(
        data=[go.Pie(labels=list(age_group_counts.keys()), values=list(age_group_counts.values()))])
    age_group_data = json.dumps(age_group_fig, cls=plotly.utils.PlotlyJSONEncoder)

    party_counts = dict(Counter(parties))
    party_fig = go.Figure(data=[go.Pie(labels=list(party_counts.keys()), values=list(party_counts.values()))])
    party_data = json.dumps(party_fig, cls=plotly.utils.PlotlyJSONEncoder)

    gender_counts = dict(Counter(genders))
    gender_fig = go.Figure(data=[go.Pie(labels=list(gender_counts.keys()), values=list(gender_counts.values()))])
    gender_data = json.dumps(gender_fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the chart data to the template
    return render(request, 'pie_chart_template.html', {
        'age_group_data': age_group_data,
        'party_data': party_data,
        'gender_data': gender_data
    })


def svg_test(request):
    return render(request, 'svg.html')