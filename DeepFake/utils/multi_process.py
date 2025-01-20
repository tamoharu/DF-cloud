from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from logging import INFO

import psutil
from tqdm import tqdm

import DeepFake.config.type as type


def run(process_frames: type.ProcessFrames, frame_paths: List[str], *args: str) -> None:
    # thread, queue = calculate_optimal_params(len(frame_paths))
    thread = 20
    queue = 1
    with tqdm(total = len(frame_paths), desc = 'processing', unit = 'frame', ascii = ' =', disable = INFO in [ 'warn', 'error' ]) as progress:
        progress.set_postfix(get_progress_info(thread, queue))
        with ThreadPoolExecutor(max_workers = thread) as executor:
            futures = []
            queue_frame_paths: Queue[str] = create_queue(frame_paths)
            queue_per_future = int(max(len(frame_paths) // thread * queue, 1))
            while not queue_frame_paths.empty():
                submit_frame_paths = pick_queue(queue_frame_paths, queue_per_future)
                future = executor.submit(process_frames, progress.update, submit_frame_paths, *args)
                futures.append(future)
            for future_done in as_completed(futures):
                future_done.result()


def create_queue(temp_frame_paths: List[str]) -> Queue[str]:
	queue: Queue[str] = Queue()
	for frame_path in temp_frame_paths:
		queue.put(frame_path)
	return queue


def pick_queue(queue: Queue[str], queue_per_future: int) -> List[str]:
	queues = []
	for _ in range(queue_per_future):
		if not queue.empty():
			queues.append(queue.get())
	return queues


def get_progress_info(max_workers: int, queue_ratio: float) -> Dict[str, Any]:
    resources = get_system_resources()
    return {
        'thread': max_workers,
        'queue': queue_ratio,
        'memory': f"{resources['memory_available']:.1f}GB",
        'cpu': f"{resources['cpu_usage']:.1f}%"
    }


def get_system_resources() -> type.SystemResources:
    cpu_count = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_io_counters()
    memory_total = memory.total / (1024 ** 3)
    memory_available = memory.available / (1024 ** 3)
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = memory.percent
    try:
        io_usage = disk.read_bytes + disk.write_bytes / disk.read_time + disk.write_time # type: ignore
    except:
        io_usage = 0.0
    return {
            'cpu_count': cpu_count,
            'memory_total': memory_total,
            'memory_available': memory_available,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'io_usage': io_usage
            }



def calculate_optimal_params(queue_items_count: int, estimated_memory_per_item: float = 0.1) -> Tuple[int, float]:
    resources = get_system_resources()
    cpu_load_factor = max(0.2, 1 - (resources['cpu_usage'] / 100))
    total_estimated_memory = queue_items_count * estimated_memory_per_item
    memory_ratio = min(1.0, resources['memory_available'] / total_estimated_memory)
    io_factor = max(0.2, 1 - (resources['io_usage'] / 100))
    optimal_threads = max(1, int(resources['cpu_count'] * cpu_load_factor * io_factor))
    optimal_queue_ratio = max(0.1, min(1.0, memory_ratio * io_factor))
    return optimal_threads, optimal_queue_ratio