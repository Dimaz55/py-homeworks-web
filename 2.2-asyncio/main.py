import asyncio
import time

import more_itertools
import aiohttp
import requests as requests
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_URL = 'https://swapi.dev/api/people/'
DB_DSN = 'sqlite+aiosqlite:///swapi.db'
BaseModel = declarative_base()
engine = create_async_engine(DB_DSN)


class StarWarsPerson(BaseModel):
    __tablename__ = 'sw_persons'

    id = Column(Integer, nullable=False, unique=True,
                primary_key=True, autoincrement=True)
    birth_year = Column(Integer, nullable=False)
    eye_color = Column(String, nullable=False)
    films = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    hair_color = Column(String, nullable=False)
    height = Column(Integer, nullable=False)
    homeworld = Column(String, nullable=False)
    mass = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    skin_color = Column(String, nullable=False)
    species = Column(String, nullable=False)
    starships = Column(String, nullable=False)
    vehicles = Column(String, nullable=False)


async def get_async_session(
    drop: bool = False, create: bool = False
):
    async with engine.begin() as conn:
        if drop:
            await conn.run_sync(BaseModel.metadata.drop_all)
            print('> Table dropped')
        if create:
            print('> Table created')
            await conn.run_sync(BaseModel.metadata.create_all)
    async_session_maker = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    return async_session_maker


async def get_person(index, session):
    print(f'Fetch person {index} START')
    async with session.get(f'{BASE_URL}{index}/') as response:
        json_data = await response.json()
        json_data.update({'id': index})
        print(f'Fetch person {index} FINISH')
        return json_data


async def get_nested_info(url, session):
    print(f'>> Get nested info from: {url}')
    async with session.get(url) as response:
        json_data = await response.json()
        return json_data.get('title') or json_data.get('name')


async def parse_response(response_json, session):
    print(f"Preparing {response_json.get('name', 'n/a')} for DB")
    excluded_fields = ['created', 'edited', 'url']
    [response_json.pop(field) for field in excluded_fields
        if field in response_json]

    parsed_data = {}
    for k, v in response_json.items():
        if isinstance(v, list) and len(v) > 0 and v[0].startswith('http'):
            nested_data_coros = (get_nested_info(url, session) for url in v)
            result = await asyncio.gather(*nested_data_coros)
            parsed_data.update({k: ', '.join(result)})
        elif isinstance(v, str) and v.startswith('http'):
            result = await get_nested_info(v, session)
            parsed_data.update({k: result})
        else:
            parsed_data.update({k: v if v else '_'})
    return parsed_data


async def insert_person_to_db(session, *param):
    res = [await parse_response(person, session) for person in param]
    session = await get_async_session(False, False)
    async with session() as db:
        for pers_data in res:
            if 'detail' in pers_data:
                continue
            swp = StarWarsPerson(**pers_data)
            db.add(swp)
            await db.commit()
            print(f'> {swp.name} added to DB')


async def async_main():
    print('Getting person count')
    response_json = requests.get(BASE_URL).json()
    person_count = response_json['count']
    print('Total:', person_count)

    await get_async_session(True, True)

    async with aiohttp.ClientSession() as session:
        person_coros = (
            get_person(index, session) for index in range(1, person_count + 1)
        )

        for person_coros_chunk in more_itertools.chunked(person_coros, 5):
            result = await asyncio.gather(*person_coros_chunk)
            await insert_person_to_db(session, *result)

if __name__ == '__main__':
    start = time.time()
    asyncio.run(async_main())
    print('COMPLETE!')
    print(time.time() - start)
