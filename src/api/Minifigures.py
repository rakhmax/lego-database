import html
from bricklink_api.catalog_item import get_item, Type
from bson.json_util import loads
from flask import request
from flask_restful import Resource
from pymongo.collection import ReturnDocument
from src.app import auth
from src.db import db


class Minifigures(Resource):
    mf_col = db.minifigures

    def get(self):
        try:
            access_string = request.headers.get('Authorization')
            user_col = db[f'mf{access_string}']

            minifigs = list(user_col.aggregate([
                {'$group' : {
                    '_id': '$itemId',
                    'itemId': { '$first': '$itemId' },
                    'image': { '$first': '$image' },
                    'name': { '$first': '$name' },
                    'price': { '$first': '$price' },
                    'categoryId': { '$first': '$categoryId' },
                    'comment': { '$first': '$comment' },
                    'year': { '$first': '$year' },
                    'count': { '$sum': 1 }
                }},
                {'$project': { '_id': 0 }}]))

            total = user_col.count_documents({})

            return {
                'minifigs': minifigs,
                'total': total
            }
        except Exception as e:
            print(e)
            return {'error': 'err'}, 500

    def post(self):
        try:
            data = loads(request.data)
            access_string = request.headers.get('Authorization')
            user_col = db[f'mf{access_string}']

            json_minifigs = get_item(
                Type.MINIFIG,
                data['itemId'],
                auth=auth)

            if json_minifigs['meta']['code'] == 400:
                raise Exception('No item with the ID')

            bricklink_data = json_minifigs['data']

            if not bricklink_data:
                raise Exception('No item with the ID')

            minifig = {
                'itemId': bricklink_data['no'],
                'name': html.unescape(bricklink_data['name']),
                'categoryId': bricklink_data['category_id'],
                'image': {
                    'base': bricklink_data['image_url'],
                    'thumbnail': bricklink_data['thumbnail_url']
                },
                'year': bricklink_data['year_released'],
                'price': float(data['price']) if data['price'] else None,
                'comment': data['comment']
            }

            inserted_minifigure = user_col.insert_one(minifig).inserted_id

            inserted_minifigure = user_col.find_one({ '_id': inserted_minifigure }, { '_id': 0 })
            inserted_minifigure['count'] = 1

            return inserted_minifigure
        except Exception as e:
            print(e)
            return {'error': 'err'}, 500

    def patch(self):
        try:
            data = loads(request.data)
            access_string = request.headers.get('Authorization')
            user_col = db[f'mf{access_string}']

            updated_minifig = user_col.find_one_and_update(
                { 'itemId': data['itemId'] },
                { '$set': data },
                { '_id': 0 },
                return_document=ReturnDocument.AFTER)

            updated_minifig['count'] = 1

            return updated_minifig
        except Exception as e:
            print(e)
            return {'error': 'err'}, 500

    def delete(self):
        try:
            lego_id = request.data.decode('utf-8')
            access_string = request.headers.get('Authorization')
            user_col = db[f'mf{access_string}']

            return user_col.find_one_and_delete({ 'itemId': lego_id }, { '_id': 0 })
        except Exception as e:
            print(e)
            return {'error': 'err'}, 500
