import os
import shutil
from pathlib import Path


def resolve_storage_paths(base_dir):
    """
    Resolve SQLite DB path and MEDIA_ROOT, preferring an attached persistent
    volume (DATA_DIR or RAILWAY_VOLUME_MOUNT_PATH) when configured.
    """
    base_dir = Path(base_dir)
    volume_dir = os.getenv('DATA_DIR', '').strip() or os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '').strip()
    data_dir = Path(volume_dir) if volume_dir else None

    sqlite_env = os.getenv('SQLITE_PATH', '').strip()
    if sqlite_env:
        db_path = Path(sqlite_env)
    elif data_dir:
        db_path = data_dir / 'db.sqlite3'
    else:
        db_path = base_dir / 'db.sqlite3'

    media_env = os.getenv('MEDIA_ROOT', '').strip()
    if media_env:
        media_root = Path(media_env)
    elif data_dir:
        media_root = data_dir / 'media'
    else:
        media_root = base_dir / 'media'

    return db_path, media_root


def bootstrap_storage(base_dir=None):
    """
    Seed an attached persistent volume with the bundled db.sqlite3 and media/
    files on first boot without ever overwriting existing persistent data.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    else:
        base_dir = Path(base_dir)

    target_db, target_media = resolve_storage_paths(base_dir)
    source_db = base_dir / 'db.sqlite3'
    source_media = base_dir / 'media'

    target_db.parent.mkdir(parents=True, exist_ok=True)
    target_media.mkdir(parents=True, exist_ok=True)

    db_seeded = False
    if target_db.resolve() != source_db.resolve() and source_db.exists() and not target_db.exists():
        tmp_db = target_db.with_name(f'.{target_db.name}.tmp')
        shutil.copy2(source_db, tmp_db)
        os.replace(tmp_db, target_db)
        db_seeded = True

    media_copied = 0
    if target_media.resolve() != source_media.resolve() and source_media.exists():
        for src in source_media.rglob('*'):
            if src.is_file():
                rel = src.relative_to(source_media)
                dst = target_media / rel
                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    media_copied += 1

    return {
        'db_path': str(target_db),
        'media_root': str(target_media),
        'db_seeded': db_seeded,
        'media_copied': media_copied,
    }


if __name__ == '__main__':
    info = bootstrap_storage()
    print(
        f"Storage ready: db={info['db_path']} (seeded={info['db_seeded']}), "
        f"media={info['media_root']} (copied={info['media_copied']})"
    )
