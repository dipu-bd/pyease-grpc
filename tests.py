import json
import os

from pyease_grpc import Protobuf, RpcSession
from pyease_grpc.rpc_uri import RpcUri

base_url = 'https://api.wuxiaworld.com'

source_dir = os.path.abspath(os.path.dirname(__file__))
proto_file = os.path.join(source_dir, 'tests', 'wuxia.proto')
descriptor_file = os.path.join(source_dir, 'tests', 'descriptor.json')


def test_protobuf():
    try:
        with open(proto_file, 'r') as f:
            proto_string = f.read()
        protobuf = Protobuf.from_proto(proto_string)
    except ModuleNotFoundError as e:
        print(str(e))
        print('Fallback to using descriptor json.')
        with open(descriptor_file, 'r') as f:
            protobuf = Protobuf.restore(json.load(f))

    data = protobuf.save()
    print('proto dependencies', '=', len(data['file']))

    with open(descriptor_file, 'w') as f:
        json.dump(data, f)

    return Protobuf.restore(data)


def get_novel(session: RpcSession, slug: str):
    return session.request(
        RpcUri(base_url, package='wuxiaworld.api.v2',
               service='Novels', method='GetNovel'),
        {'slug': slug},
    ).single


def get_chapters(session: RpcSession, novel_id: int):
    return session.request(
        RpcUri(base_url,  package='wuxiaworld.api.v2',
               service='Chapters', method='GetChapterList'),
        {'novelId': novel_id},
    ).single


if __name__ == '__main__':
    protobuf = test_protobuf()
    session = RpcSession(protobuf)
    print('-' * 20)
    novel = get_novel(session, 'a-will-eternal')
    print(novel)
    print('-' * 20)
    assert novel and novel['item']
    chapters = get_chapters(session, novel['item']['id'])
    assert chapters and chapters['items']
    print('items', '=', len(chapters['items']))
    print('first', '=', chapters['items'][0])
