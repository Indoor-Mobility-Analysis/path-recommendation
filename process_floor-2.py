from process_frame_noplt import FrameProcess
from pymongo import MongoClient

map_path = './new_map/mask_floor-2.csv'
exits_path = './new_mapexit_floor-2.csv'
gates_path = './new_map/admiralty_gates.txt'

client = MongoClient()

db = client.mapping

collection = db.people_activity_path

a = collection.find({'floor': -2 })

number = 0
for record in a:
    try:
        model = FrameProcess()

        new = model.process_one_frame_floorX(record, exits_path=exits_path, \
                                             map_path=map_path, \
                                             print_or_not=False)
        # model.plot_results()
        collection.update_one({u'_id':record[u'_id']}, {'$set':{'small_clusters':new}})
        # number += 1
    except Exception, ee:
        print record['_id'], str(ee)
    number += 1

    print number
#     if number == 5:
#         break
