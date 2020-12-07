from sacred import Ingredient
from torchvision import transforms
from torch.utils.data import DataLoader

from ..utils import ExpandedRandomSampler, check_overlap

dataset_ingredient = Ingredient('dataset')

test_transform = transforms.ToTensor()


@dataset_ingredient.config
def config():
    data_path = 'data'
    split = 0
    fold = 0
    preload = True
    batch_size = 64
    shuffle = True
    num_workers = 8
    drop_last = True
    pin_memory = True


@dataset_ingredient.named_config
def glas():
    data_path = 'data/GlaS'
    name = 'glas'
    folds_dir = 'folds/glas'
    batch_size = 16
    patch_size = 416
    sampler_mul = 8


@dataset_ingredient.named_config
def camelyon16():
    name = 'camelyon16'
    folds_dir = 'folds/camelyon16'
    preload = False
    size = 512


@dataset_ingredient.capture
def load_glas(folds_dir, split, fold, data_path, preload, patch_size, batch_size, shuffle, sampler_mul,
              num_workers, drop_last, pin_memory):
    from .dataset import PhotoDataset
    from ..localization.glas.utils import get_files, decode_classes

    files = get_files(folds_dir, split, fold)
    train_files, valid_files, test_files = [decode_classes(f) for f in files]
    check_overlap(train_files, valid_files, test_files)

    train_loader = DataLoader(
        PhotoDataset(
            data_path=data_path,
            files=train_files,
            patch_size=patch_size,
            augment=True,
            rotate=True,
            transform=transforms.Compose([
                transforms.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.5, hue=0.05),
                transforms.ToTensor(),
            ]),
            mask_transform=transforms.ToTensor(),
            preload=preload
        ),
        batch_size=batch_size,
        num_workers=num_workers,
        sampler=ExpandedRandomSampler(len(train_files), sampler_mul),
        pin_memory=pin_memory,
        drop_last=drop_last
    )
    valid_loader = DataLoader(
        PhotoDataset(data_path=data_path, files=valid_files,
                     transform=test_transform, mask_transform=test_transform, preload=preload),
        batch_size=1, num_workers=1,
        shuffle=shuffle,
        pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        PhotoDataset(data_path=data_path, files=test_files,
                     transform=test_transform, mask_transform=test_transform, preload=preload),
        batch_size=1, num_workers=1,
        pin_memory=pin_memory,
    )
    return train_loader, valid_loader, test_loader


@dataset_ingredient.capture
def load_camelyon16(folds_dir, size, split, fold, data_path, preload, batch_size, shuffle,
                    num_workers, drop_last, pin_memory):
    from .dataset import PhotoDataset
    from ..localization.camelyon16.utils import get_files, decode_classes

    files = get_files(folds_dir, size, split, fold)
    train_files, valid_files, test_files = [decode_classes(f) for f in files]
    check_overlap(train_files, valid_files, test_files)

    # TODO: check with data

    train_loader = DataLoader(
        PhotoDataset(
            data_path=data_path,
            files=train_files,
            augment=True,
            rotate=True,
            transform=test_transform,
            mask_transform=test_transform,
            preload=preload
        ),
        batch_size=batch_size,
        num_workers=num_workers,
        shuffle=shuffle,
        pin_memory=pin_memory,
        drop_last=drop_last
    )
    valid_loader = DataLoader(
        PhotoDataset(data_path=data_path, files=valid_files,
                     transform=test_transform, mask_transform=test_transform, preload=preload),
        batch_size=1, num_workers=4,
        shuffle=shuffle,
        pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        PhotoDataset(data_path=data_path, files=test_files,
                     transform=test_transform, mask_transform=test_transform),
        batch_size=1, num_workers=4,
        pin_memory=pin_memory,
    )
    return train_loader, valid_loader, test_loader


_dataset_loaders = {
    'glas': load_glas,
    'camelyon16': load_camelyon16,
}


@dataset_ingredient.capture
def load_dataset(name):
    return _dataset_loaders[name]()
