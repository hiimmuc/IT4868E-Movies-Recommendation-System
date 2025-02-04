import importlib
import os
import random

import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml


# Load a YAML configuration file
def load_config(path):
    """
    Tải cấu hình từ tệp YAML.
    Tham số:
    path (str): Đường dẫn tới tệp YAML chứa cấu hình.
    Trả về:
    dict: Cấu hình được tải từ tệp YAML.
    """

    with open(path) as f:
        config_yaml = yaml.safe_load(f)
    return config_yaml


# Import an object from a string path
def import_object(path):
    # Nhập một đối tượng từ một đường dẫn chuỗi
    module_path, obj_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, obj_name)


# Get the optimizer, scheduler, and scaler
def create_optimizer_scheduler_scaler(config_yaml, model):
    # Tạo optimizer, scheduler, và scaler từ cấu hình
    training_config = config_yaml["train"]
    # Optimizer
    optimizer_class = import_object(training_config["optimizer"]["type"])
    optimizer_params = training_config["optimizer"]["params"]
    optimizer = optimizer_class(model.parameters(), **optimizer_params)

    # Scheduler
    scheduler = None  # Default value if no scheduler is provided
    if "scheduler" in training_config:  # Check if scheduler is in config
        scheduler_class = import_object(training_config["scheduler"]["type"])
        scheduler_params = training_config["scheduler"]["params"]
        scheduler = scheduler_class(optimizer, **scheduler_params)

    # AMP (Automatic Mixed Precision)
    use_amp = training_config.get("amp", False)  # Default to False if not specified
    if use_amp:
        scaler = torch.amp.GradScaler()  # Create GradScaler for AMP
    else:
        scaler = None  # No AMP, no scaler

    return optimizer, scheduler, scaler


def remove_label_edges(batch):
    # print(type(output))
    movie_user_edge = batch["movie", "ratedby", "user"]
    edge_index = movie_user_edge.edge_index
    edge_label_index = movie_user_edge.edge_label_index

    edge_label_set = edge_label_index.t().unsqueeze(1)  # Shape: [n, 1, 2]
    edges = edge_index.t().unsqueeze(0)  # Shape: [1, m, 2]

    # So khớp tất cả cạnh trong edge_index với edge_label_index
    matches = (edges == edge_label_set).all(dim=2)  # Shape: [n, m]

    # Kiểm tra xem mỗi cạnh trong edge_index có khớp với ít nhất một cạnh trong edge_label_index
    mask = ~matches.any(dim=0)  # Shape: [m], True nếu cạnh không khớp
    movie_user_edge.edge_index = edge_index[:, mask]
    if getattr(movie_user_edge, "pos", None) is not None:
        movie_user_edge.pos = movie_user_edge.pos[mask]
    movie_user_edge.rating = movie_user_edge.rating[mask]
    if getattr(movie_user_edge, "weight", None) is not None:
        movie_user_edge.weight = movie_user_edge.weight[mask]
    movie_user_edge.e_id = movie_user_edge.e_id[mask]
    return batch


def set_seed(seed=0):
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"


def save_checkpoint(
    model,
    optimizer,
    scheduler,
    scaler,
    epoch,
    end_epoch,
    train_loss,
    val_loss,
    val_acc,
    val_f1,
    model_path,
    config,
    log_dir,
    train_losses,
    val_losses,
):
    """
    Lưu toàn bộ mô hình và các thông số huấn luyện vào file checkpoint.

    Args:
        model: Mô hình PyTorch (hoặc bất kỳ mô hình nào).
        optimizer: Optimizer (Ví dụ: Adam, SGD, ...).
        scheduler: Scheduler (Ví dụ: Learning rate scheduler).
        scaler: Scaler dùng cho mixed precision training.
        epoch: Số epoch hiện tại.
        train_loss: Giá trị train loss.
        val_loss: Giá trị validation loss.
        val_acc: Accuracy trên validation.
        val_f1: F1 score trên validation.
        model_path: Đường dẫn đến file lưu checkpoint.
        config: Cấu hình huấn luyện.
    """
    checkpoint = {
        "model": model,  # Thông số mô hình
        "optimizer": optimizer,  # Thông số optimizer
        "scheduler": scheduler,  # Thông số scheduler
        "scaler": scaler,  # Thông số scaler (nếu có)
        "epoch": epoch,  # Số epoch hiện tại
        "end_epoch": end_epoch,  # Số epoch kết thúc
        "train_loss": train_loss,  # Giá trị train loss
        "val_loss": val_loss,  # Giá trị validation loss
        "val_acc": val_acc,  # Accuracy trên validation
        "val_f1": val_f1,  # F1 score trên validation
        "config": config,  # Cấu hình huấn luyện
        "log_dir": log_dir,  # Thư mục lưu log
        "train_losses": train_losses,  # List train loss qua các epoch
        "val_losses": val_losses,  # List validation loss
    }
    torch.save(checkpoint, model_path)


def save_checkpoint2(
    model,
    optimizer,
    scheduler,
    scaler,
    epoch,
    end_epoch,
    train_loss,
    val_loss,
    rank_k,
    f1_k,
    precision_k,
    recall_k,
    nDCG_k,
    model_path,
    config,
    log_dir,
    train_losses,
    val_losses,
):
    """
    Lưu toàn bộ mô hình và các thông số huấn luyện vào file checkpoint.

    Args:
        model: Mô hình PyTorch (hoặc bất kỳ mô hình nào).
        optimizer: Optimizer (Ví dụ: Adam, SGD, ...).
        scheduler: Scheduler (Ví dụ: Learning rate scheduler).
        scaler: Scaler dùng cho mixed precision training.
        epoch: Số epoch hiện tại.
        train_loss: Giá trị train loss.
        val_loss: Giá trị validation loss.
        val_acc: Accuracy trên validation.
        val_f1: F1 score trên validation.
        model_path: Đường dẫn đến file lưu checkpoint.
        config: Cấu hình huấn luyện.
    """
    checkpoint = {
        "model": model,  # Thông số mô hình
        "optimizer": optimizer,  # Thông số optimizer
        "scheduler": scheduler,  # Thông số scheduler
        "scaler": scaler,  # Thông số scaler (nếu có)
        "epoch": epoch,  # Số epoch hiện tại
        "end_epoch": end_epoch,  # Số epoch kết thúc
        "train_loss": train_loss,  # Giá trị train loss
        "val_loss": val_loss,  # Giá trị validation loss
        "rank@k": rank_k,  # Rank@k trên validation
        "val_f1@k": f1_k,  # F1 score trên validation
        "precision@k": precision_k,  # Precision score trên validation
        "recall@k": recall_k,  # Recall score trên validation
        "val_nDCG@k": nDCG_k,  # NDCG score trên validation
        "config": config,  # Cấu hình huấn luyện
        "log_dir": log_dir,  # Thư mục lưu log
        "train_losses": train_losses,  # List train loss qua các epoch
        "val_losses": val_losses,  # List validation loss
    }
    torch.save(checkpoint, model_path)


def load_checkpoint(save_path):
    """
    Load checkpoint từ file.

    Args:
        save_path: Đường dẫn đến file checkpoint.

    Returns:
        checkpoint: Dữ liệu trong checkpoint.
    """
    checkpoint = torch.load(save_path)
    return checkpoint


def save_loss_plot(train_losses, val_losses, file_path):
    plt.figure(figsize=(10, 5))
    plt.plot(
        range(len(train_losses)),
        train_losses,
        label="Train Loss",
        color="blue",
        marker="o",
        linestyle="-",
    )
    plt.plot(
        range(len(val_losses)),
        val_losses,
        label="Validation Loss",
        color="orange",
        marker="o",
        linestyle="-",
    )
    plt.xlabel("Epoch")
    plt.xticks(range(len(train_losses)))
    plt.ylabel("Loss")
    plt.title("Training and Validation Loss over Epochs")
    plt.legend()
    plt.grid(True)

    plt.savefig(file_path)
    plt.close()


def map_edge_index_to_original_with_list(edge_index, node_id1, node_id2):
    edge_index_mapped = torch.stack([node_id1[edge_index[0]], node_id2[edge_index[1]]], dim=0)
    return edge_index_mapped


def check_overlap(train_data, val_data, test_data):
    # Lấy edge_label_index từ các tập dữ liệu

    train_edges = map_edge_index_to_original_with_list(
        train_data[("movie", "ratedby", "user")].edge_label_index,
        train_data["movie"].node_id,
        train_data["user"].node_id,
    )
    val_edges = map_edge_index_to_original_with_list(
        val_data[("movie", "ratedby", "user")].edge_label_index,
        val_data["movie"].node_id,
        val_data["user"].node_id,
    )
    test_edges = map_edge_index_to_original_with_list(
        test_data[("movie", "ratedby", "user")].edge_label_index,
        test_data["movie"].node_id,
        test_data["user"].node_id,
    )

    # Chuyển các edge_label_index thành tập hợp (set) để dễ so sánh
    train_edges_set = set(map(tuple, train_edges.T.tolist()))
    val_edges_set = set(map(tuple, val_edges.T.tolist()))
    test_edges_set = set(map(tuple, test_edges.T.tolist()))

    # Kiểm tra overlap giữa tập train và val
    val_overlap = train_edges_set.intersection(val_edges_set)
    test_overlap = train_edges_set.intersection(test_edges_set)

    # In ra kết quả
    print(f"Number of overlapping edges in train and val: {len(val_overlap)}")
    print(f"Number of overlapping edges in train and test: {len(test_overlap)}")

    if val_overlap:
        print("Overlapping edges in train and val:", val_overlap)
    if test_overlap:
        print("Overlapping edges in train and test:", test_overlap)


def min_max_scale(x: torch.Tensor, min_val: float, max_val: float) -> torch.Tensor:
    """
    Scale dữ liệu từ [min_val, max_val] về [0, 1].

    Args:
        x (torch.Tensor): Tensor dữ liệu cần scale.
        min_val (float): Giá trị tối thiểu trong khoảng ban đầu.
        max_val (float): Giá trị tối đa trong khoảng ban đầu.

    Returns:
        torch.Tensor: Tensor sau khi scale về [0, 1].
    """
    return (x - min_val) / (max_val - min_val)


if __name__ == "__main__":
    from pathlib import Path

    # get last checkpoint dir from runs/
    ckpt_path = Path("runs").rglob("best.pt")
    ckpt = load_checkpoint(ckpt_path)
    model = ckpt["model"]
    optimizer = ckpt["optimizer"]
    scheduler = ckpt["scheduler"]
    scaler = ckpt["scaler"]
    epoch = ckpt["epoch"]
    print(model)
    print(f"optimizer: {optimizer}")
    print(f"scheduler: {scheduler}")
    print(f"scaler: {scaler}")
    print(f"epoch: {epoch}")
