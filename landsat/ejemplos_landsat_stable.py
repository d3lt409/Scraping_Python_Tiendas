import requests
import json

def request(self, request_code, **kwargs):
        """Perform a request to the EE API.
        Possible request codes are listed here:
        https://m2m.cr.usgs.gov/api/docs/json/
        """
        url = self.endpoint + request_code
        if 'apiKey' not in kwargs:
            kwargs.update(apiKey=self.key)
        params = to_json(**kwargs)
        response = requests.get(url, params=params).json()
        if response['error']:
            raise EarthExplorerError('EE: {}'.format(response['error']))
        else:
            return response['data']

def search(
            dataset,
            latitude=None,
            longitude=None,
            bbox=None,
            max_cloud_cover=None,
            start_date=None,
            end_date=None,
            months=None,
            max_results=20):

        params = {
            'datasetName': dataset,
            'includeUnknownCloudCover': False,
            'maxResults': max_results
        }

        if latitude and longitude:
            params.update(spatialFilter=spatial_filter(longitude, latitude))
        if bbox:
            params.update(spatialFilter=spatial_filter(*bbox))
        if max_cloud_cover:
            params.update(maxCloudCover=max_cloud_cover)
        if start_date:
            params.update(temporalFilter=temporal_filter(start_date, end_date))
        if months:
            params.update(months=months)

        response = request('scene-search', **params)
        return response['results']


username = 'manuelfer1996@gmail.com'
password = 'Nazlyman12345'

URL = 'https://m2m.cr.usgs.gov/api/api/json/stable/'

data = json.dumps({"username":username, "password":password, "catalogID":'EE'})
response = requests.post(URL + 'login?', data=data).json()

