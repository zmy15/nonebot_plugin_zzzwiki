import os
import json
import nonebot
import yaml
import difflib
from .config import Config
from nonebot.permission import SUPERUSER
from nonebot import on_endswith, on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
from .resource import git_clone, git_pull

guide_image = on_endswith("攻略", ignorecase=False)
pokedex_image = on_endswith("图鉴", ignorecase=False)
download_resources = on_command("下载zzz资源", permission=SUPERUSER, block=True)
update_resources = on_command("更新zzz资源", permission=SUPERUSER, block=True)

global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config.dict())

repo_url = 'https://github.com/Nwflower/zzz-atlas.git'
resources_path = config.resources_path
git_path = resources_path.removesuffix('/zzzwiki')


def load_file():
    file_name = 'path.json'
    file_path = os.path.join(resources_path, file_name)
    if not os.path.exists(file_path):
        try:
            if not git_pull():
                if not git_clone(repo_url, git_path):
                    return False
        except:
            if not git_clone(repo_url, git_path):
                return False
    # 读取 path.json 文件
    with open(file_path, 'r', encoding='utf-8') as f:
        path_data = json.load(f)
    return path_data


# 读取角色别名
def load_aliases(file_name) -> dict:
    file_path = os.path.join(resources_path, file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        aliases = yaml.safe_load(f)
    return aliases


def load_path(key) -> dict:
    if key == '角色攻略':
        aliases_path_guide = load_file()['othername']['角色攻略']
        aliases_guide = load_aliases(aliases_path_guide.lstrip('/'))
        return aliases_guide
    elif key == '音擎':
        aliases_path_audio = load_file()['othername']['音擎']
        aliases_audio = load_aliases(aliases_path_audio.lstrip('/'))
        return aliases_audio
    elif key == '驱动盘':
        aliases_path_record = load_file()['othername']['驱动盘']
        aliases_record = load_aliases(aliases_path_record.lstrip('/'))
        return aliases_record


@download_resources.handle()
async def handle_download_resources(bot: Bot, event: Event):
    if git_clone(repo_url, resources_path):
        await bot.send(event, "资源下载成功")
    else:
        await bot.send(event, "资源下载失败，可能是网络问题或资源已存在")


@update_resources.handle()
async def handle_update_resources(bot: Bot, event: Event):
    if git_pull():
        await bot.send(event, "资源更新成功")
    else:
        await bot.send(event, "资源更新失败，可能是网络问题或没有下载资源")


@guide_image.handle()
async def handle_send_image(bot: Bot, event: Event):
    if not load_file():
        await bot.finish(event, "资源不存在，请尝试重新下载或手动clone")
    message_text = event.get_message().extract_plain_text().strip()
    if message_text.endswith("攻略"):
        character_name = message_text[:-2].strip()

        # 收集所有角色名及别名进行模糊匹配
        all_names = list(load_file()['角色攻略'].keys()) + sum(filter(None, load_path('角色攻略').values()), [])
        closest_matches = difflib.get_close_matches(character_name, all_names, n=1, cutoff=0.6)
        if closest_matches:
            matched_name = closest_matches[0]
            for main_name, alias_list in load_path('角色攻略').items():
                if matched_name == main_name or matched_name in (alias_list or []):
                    character_name = main_name
                    break
            else:
                character_name = matched_name
        else:
            return
        await send_image(bot, event, "角色攻略", character_name)


@pokedex_image.handle()
async def handle_send_pokedex_image(bot: Bot, event: Event):
    if not load_file():
        await bot.finish(event, "资源不存在，请尝试重新下载或手动clone")
    message_text = event.get_message().extract_plain_text().strip()
    if message_text.endswith("图鉴"):
        name = message_text[:-2].strip()

        all_names = (list(load_file()['角色'].keys()) + list(load_file()['音擎'].keys())
                     + sum(filter(None, load_path('角色攻略').values()), [])
                     + sum(filter(None, load_path('音擎').values()), []))
        closest_matches = difflib.get_close_matches(name, all_names, n=1, cutoff=0.6)
        if closest_matches:
            matched_name = closest_matches[0]
            for main_name, alias_list in load_path('音擎').items():
                if matched_name == main_name or matched_name in alias_list:
                    name = main_name
                    break
            else:
                name = matched_name

            if name in load_file()['角色']:
                await send_image(bot, event, "角色", name)
            elif name in load_file()['音擎']:
                await send_image(bot, event, "音擎", name)
            # elif name in load_file()['驱动盘']:
            #     await send_image(bot, event, "驱动盘", name)


async def send_image(bot: Bot, event: Event, category: str, name: str):
    if name in load_file()[category]:
        image_path = load_file()[category][name].lstrip('/')
        full_image_path = os.path.join(resources_path, image_path).replace('/', '\\')
        if os.path.exists(full_image_path):
            await bot.send(event, MessageSegment.image(f"file:///{full_image_path}"))
