import os
import shutil
import random
import re
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

IMG_FOLDER = "profile_results_img"
DATA_DIR = "data"

def split_images(source_dir):
    print("Generating datasets…")
    data_dir = DATA_DIR
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'val')
    eval_dir = os.path.join(data_dir, 'eval')

    for dir_path in [data_dir, train_dir, val_dir, eval_dir]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path)

    for class_name in os.listdir(source_dir):
        class_path = os.path.join(source_dir, class_name)
        
        if not os.path.isdir(class_path):
            continue

        os.makedirs(os.path.join(train_dir, class_name), exist_ok=True)
        os.makedirs(os.path.join(val_dir, class_name), exist_ok=True)
        os.makedirs(os.path.join(eval_dir, class_name), exist_ok=True)

        files = [f for f in os.listdir(class_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        
        images = sorted(files, key=lambda f: [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', f)])
        
        total_images = len(images)

        if class_name == "other":
            train_split = int(total_images * 0.5)
            val_split = int(total_images * 0.25)
            eval_split = total_images - train_split - val_split
        else:
            train_split = int(total_images * 0.8)
            val_split = int(total_images * 0.1)
            eval_split = total_images - train_split - val_split

        train_images = images[:train_split]
        val_images = images[train_split : train_split + val_split]
        eval_images = images[train_split + val_split :]

        for img_name in train_images:
            shutil.copy(os.path.join(class_path, img_name), os.path.join(train_dir, class_name, img_name))
        
        for img_name in val_images:
            shutil.copy(os.path.join(class_path, img_name), os.path.join(val_dir, class_name, img_name))

        for img_name in eval_images:
            shutil.copy(os.path.join(class_path, img_name), os.path.join(eval_dir, class_name, img_name))

    print("Datasets (train, val, eval) were generated.")

split_images(IMG_FOLDER)

data_transforms = {
    'train': transforms.Compose([
        transforms.ToTensor(),
    ]),
    'val': transforms.Compose([
        transforms.ToTensor(),
    ]),
    'eval': transforms.Compose([
        transforms.ToTensor(),
    ]),
}

image_datasets = {x: datasets.ImageFolder(os.path.join(DATA_DIR, x), data_transforms[x]) for x in ['train', 'val', 'eval']}

dataloaders = {x: DataLoader(image_datasets[x], batch_size=32, shuffle=True, num_workers=4) for x in ['train', 'val', 'eval']}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val', 'eval']}
class_names = image_datasets['train'].classes
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

print("Class name:", class_names)
print("Train data size:", dataset_sizes['train'])
print("Val data size:", dataset_sizes['val'])
print("Eval data size:", dataset_sizes['eval'])

model_ft = models.resnet18(weights=None)

num_ftrs = model_ft.fc.in_features
model_ft.fc = nn.Linear(num_ftrs, len(class_names))
model_ft = model_ft.to(device)

criterion = nn.CrossEntropyLoss()
optimizer_ft = optim.SGD(model_ft.parameters(), lr=0.01, momentum=0.9)

from torch.optim import lr_scheduler
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)

import time
import copy

def train_model(model, criterion, optimizer, scheduler, num_epochs=10):
    since = time.time()
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch+1, num_epochs))
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)
                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            if phase == 'train':
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(running_corrects.double(), dataset_sizes[phase])

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(
                phase, epoch_loss, epoch_acc))

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))

    model.load_state_dict(best_model_wts)
    return model

model_ft = train_model(model_ft, criterion, optimizer_ft, exp_lr_scheduler, num_epochs=10)
torch.save(model_ft.state_dict(), 'model_websites_classifier.pth')

model_ft.eval()

def get_predictions(model, dataloader):
    model.eval()
    predictions = []
    true_labels = []
    
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            
            predictions.extend(preds.cpu().numpy())
            true_labels.extend(labels.cpu().numpy())
            
    return predictions, true_labels

from sklearn.metrics import confusion_matrix
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

predictions, true_labels = get_predictions(model_ft, dataloaders['eval'])

cm = confusion_matrix(true_labels, predictions)
np.save('cm_websites.npy', cm)

def file_name_to_url(url: str) -> str:
    return url.replace("_", ".")

urls = [x.replace("_", ".") for x in class_names]

print("Confusion Matrix:\n", cm)

cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
cm_normalized = np.nan_to_num(cm_normalized)

plt.figure(figsize=(15, 12))
sns.heatmap(cm_normalized, fmt='.2f', cmap='Greys', linewidths=0,
            xticklabels=urls, yticklabels=urls)
plt.xlabel('Predicted Website', fontsize=12)
plt.ylabel('Actual Website', fontsize=12)

plt.xticks(rotation=90, ha='right')
plt.yticks(rotation=0)

plt.tight_layout()
plt.savefig('confusion_matrix.png')
plt.close()
