"""
Генерирует тестовые данные для БД
made by GIGAChat
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import asyncio
import random
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.models import Model
from src.api.organizations.models import Organization
from src.api.organizations.models import Building
from src.api.organizations.models import Activity
from src.api.organizations.models import Phone


# Настройка БД
DATABASE_URL = "sqlite+aiosqlite:///./data/compendium.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def fake_address():
    streets = [
        "Ленина", "Гагарина", "Мира", "Энтузиастов", "Пушкина", "Садовая",
        "Кирова", "Тургенева", "Жукова", "Чехова", "Лермонтова", "Радио",
        "Вавилова", "Космонавтов", "Баумана", "Новослободская"
    ]
    street = random.choice(streets)
    number = random.randint(1, 100)
    return f"г. Москва, ул. {street}, {number}"


def fake_name():
    prefixes = ["Торг", "Сервис", "Центр", "Мастер", "Профи", "Евро", "Мега", "Супер", "Альфа", "Омега", "Нано", "Квант"]
    cores = ["Сервис", "Групп", "Лайн", "Тех", "Сеть", "Маркет", "Плюс", "Холдинг", "Системс", "Банк", "Фуд", "Фреш", "Лайф"]
    return f"{random.choice(prefixes)}{random.choice(cores)}"


def fake_phone():
    return f"+7 9{random.randint(10, 99)} {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"


async def main():
    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

    async with async_session() as db:
        print("🌍 Создаём 20 зданий...")
        buildings = []
        base_lat = 55.75
        base_lng = 37.61
        for i in range(20):
            lat = round(base_lat + random.uniform(-0.02, 0.02), 5)
            lng = round(base_lng + random.uniform(-0.02, 0.02), 5)
            b = Building(
                address=fake_address(),
                latitude=lat,
                longitude=lng
            )
            buildings.append(b)
            db.add(b)
        await db.commit()
        print("✅ Здания созданы")

        # Назначим ID
        for b in buildings:
            await db.refresh(b)

        print("📁 Создаём дерево из 5 корневых видов деятельности...")
        root_names = ["Еда", "Образование", "Финансы", "Медицина", "Транспорт"]
        roots = []

        for name in root_names:
            act = Activity(name=name, parent_id=None)
            db.add(act)
            roots.append(act)

        await db.commit()
        print("✅ Корни созданы")

        all_activities = []

        for root in roots:
            await db.refresh(root)
            all_activities.append(root)

            # Уровень 2: 1–3 подвида
            num_level2 = random.randint(1, 3)
            level2_acts = []

            for _ in range(num_level2):
                act = Activity(
                    name=f"{root.name} - {fake_name()}",
                    parent_id=root.id
                )
                db.add(act)
                level2_acts.append(act)
                all_activities.append(act)

            await db.commit()

            # Уровень 3: для каждого level2 — 1–3 подвида
            for lvl2_act in level2_acts:
                await db.refresh(lvl2_act)
                num_level3 = random.randint(1, 3)
                for _ in range(num_level3):
                    act = Activity(
                        name=f"{lvl2_act.name} - {fake_name()}",
                        parent_id=lvl2_act.id
                    )
                    db.add(act)
                    all_activities.append(act)

            await db.commit()

        print("✅ Дерево активностей построено")

        # Обновим все ID
        for act in all_activities:
            await db.refresh(act)

        print("🏢 Создаём 150 организаций...")
        organizations = []
        for i in range(150):
            org = Organization(
                name=fake_name(),
                building_id=random.choice(buildings).id
            )
            db.add(org)
            organizations.append(org)

        await db.commit()
        print("✅ Организации созданы")

        for org in organizations:
            await db.refresh(org)

        print("📞 Добавляем 1–2 телефона каждой организации...")
        phones = []
        for org in organizations:
            num_phones = random.randint(1, 2)
            for _ in range(num_phones):
                phone = Phone(
                    number=fake_phone(),
                    organization_id=org.id
                )
                phones.append(phone)
                db.add(phone)

        await db.commit()
        print("✅ Телефоны добавлены")

        print("🔗 Связываем организации с 1–2 видами деятельности...")
        activity_ids = [act.id for act in all_activities]
        for org in organizations:
            num_activities = random.randint(1, 2)
            chosen_ids = random.sample(activity_ids, num_activities)
            # Загружаем активности
            result = await db.execute(select(Activity).where(Activity.id.in_(chosen_ids)))
            acts = result.scalars().all()
            org.activities.extend(acts)

        await db.commit()
        print("✅ Связи с деятельностью созданы")

        print("🎉 Готово! База данных заполнена тестовыми данными.")
        print(f"  • Здания: 20")
        print(f"  • Организации: 150")
        print(f"  • Телефоны: {len(phones)}")
        print(f"  • Виды деятельности: {len(all_activities)}")
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
