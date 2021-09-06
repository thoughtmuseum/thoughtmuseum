import time
import requests
import json
from Thoughtmuseum.settings import ZOOM_API_KEY, ZOOM_API_SECRET
import jwt


class ZoomAPI:
    MEETINGS_URL = 'https://api.zoom.us/v2/users/{}/meetings'
    USERS_URL = 'https://api.zoom.us/v2/users'
    RECORDINGS_URL = 'https://api.zoom.us/v2/meetings/{}/recordings'
    DELETE_MEETING_URL = 'https://api.zoom.us/v2/meetings/{}'

    @staticmethod
    def _encode_auth_token():
        return jwt.encode({'iss': ZOOM_API_KEY, 'exp': int(time.time()) + 5000}, ZOOM_API_SECRET)

    def _get_headers(self):
        payload = self._encode_auth_token().decode('ascii')
        headers = {'Authorization': 'Bearer {}'.format(str(payload)),
                   'Content-Type': 'application/json'}
        return headers

        # makes call to api and returns join_url

    def create_meeting(self, start_time, timezone, topic, host_id):
        data_dict = {'type': '2', 'duration': '60', 'settings': {'join_before_host': 'true',
                                                                 'audio': 'both',
                                                                 'host_video': 'true',
                                                                 'participant_video': 'true',
                                                                 'mute_upon_entry': 'false'}, 'topic': topic,
                     'start_time': start_time, 'timezone': timezone}
        # add dynamic options
        # make the call
        response = requests.post(self.MEETINGS_URL.format(host_id), data=json.dumps(data_dict, separators=(',', ':')),
                                 headers=self._get_headers())
        
        # return join_url string
        #return {'start_url': 'https://zoom.us/test', 'join_url': 'https://zoom.us/test'}

        return response.json()

    def get_users(self):
        response = requests.get(self.USERS_URL, headers=self._get_headers())
       
        return response.json()['users']

    def create_user(self, user):
        data = {
            "action": "custCreate",
            "user_info": {
                "type": 1,
                "email": user.email.lower(),
                "first_name" : user.first_name,
                "last_name" : user.last_name,
            }
        }
        response = requests.post(self.USERS_URL,
                                 data=json.dumps(data, separators=(',', ':')), headers=self._get_headers())
        print(response.content)
        return response.json()['id']

    def retrieve_recordings(self, meeting_id):
        response = requests.get(self.RECORDINGS_URL.format(meeting_id), headers=self._get_headers()).json()
        return response.get('recording_files')

    def delete_meeting(self, meeting_id):
        return True
        # response = requests.delete(self.DELETE_MEETING_URL.format(meeting_id), headers=self._get_headers())
        # return response.status_code==204 or response.status_code==404
