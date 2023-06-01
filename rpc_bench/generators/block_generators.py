from __future__ import annotations

import typing

from flood import spec


def generate_block_numbers(
    n: int,
    start_block: int,
    end_block: int,
    *,
    replace: bool = False,
    sort: bool = False,
    random_seed: spec.RandomSeed | None = None,
) -> typing.Sequence[int]:
    import numpy as np

    # seed a generator
    if random_seed is None:
        random_seed = 0
    if isinstance(random_seed, int):
        gen = np.random.Generator(np.random.PCG64(random_seed))

    # generate blocks
    all_blocks = np.arange(start_block, end_block + 1)
    chosen = gen.choice(all_blocks, size=n, replace=replace)

    # sort
    if sort:
        return sorted(chosen)
    else:
        return list(chosen)


def generate_block_hashes(
    n: int,
) -> typing.Sequence[str]:
    raise NotImplementedError()


def generate_block_ranges(
    *,
    n: int,
    range_size: int,
    start_block: int,
    end_block: int,
    non_overlapping: bool = True,
    sort: bool = False,
    n_attempts: int = 1_000_000,
    random_seed: spec.RandomSeed | None = None,
    method: str = 'strides',
) -> typing.Sequence[tuple[int, int]]:
    if method == 'strides':
        return _generate_block_ranges_strides(
            n=n,
            range_size=range_size,
            start_block=start_block,
            end_block=end_block,
            non_overlapping=non_overlapping,
            sort=sort,
            n_attempts=n_attempts,
            random_seed=random_seed,
        )
    elif method == 'individual':
        return _generate_block_ranges_individual(
            n=n,
            range_size=range_size,
            start_block=start_block,
            end_block=end_block,
            non_overlapping=non_overlapping,
            sort=sort,
            n_attempts=n_attempts,
            random_seed=random_seed,
        )
    else:
        raise Exception('unknown method: ' + str(method))


def _generate_block_ranges_strides(
    *,
    n: int,
    range_size: int,
    start_block: int,
    end_block: int,
    non_overlapping: bool = True,
    sort: bool = False,
    n_attempts: int = 1_000_000,
    random_seed: spec.RandomSeed | None = None,
) -> typing.Sequence[tuple[int, int]]:
    import numpy as np

    if random_seed is None:
        random_seed = 0
    if isinstance(random_seed, int):
        gen = np.random.Generator(np.random.PCG64(random_seed))

    block_ranges: list[tuple[int, int]] = []
    while len(block_ranges) < n:
        random_phases = list(range(range_size))
        gen.shuffle(random_phases)
        for random_phase in random_phases:
            strides = np.arange(start_block + random_phase, end_block, range_size)
            gen.shuffle(strides)
            n_missing = n - len(block_ranges)
            if n_missing > 0:
                for stride in strides[:n_missing]:
                    block_ranges.append((stride, stride + range_size))
            else:
                break

    return block_ranges


def _generate_block_ranges_individual(
    *,
    n: int,
    range_size: int,
    start_block: int,
    end_block: int,
    non_overlapping: bool = True,
    sort: bool = False,
    n_attempts: int = 1_000_000,
    random_seed: spec.RandomSeed | None = None,
) -> typing.Sequence[tuple[int, int]]:
    import numpy as np

    # seed a generator
    if random_seed is None:
        random_seed = 0
    if isinstance(random_seed, int):
        gen = np.random.Generator(np.random.PCG64(random_seed))

    # create starting sample
    start_blocks = generate_block_numbers(
        n=n,
        start_block=start_block,
        end_block=end_block,
        replace=non_overlapping,
    )
    candidates = iter(start_blocks)

    # create ranges
    attempt = 0
    ranges: set[tuple[int, int]] = set()
    while len(ranges) < n:
        # record attempt
        attempt += 1
        if attempt > n_attempts:
            raise Exception(
                'could not find block range set after '
                + str(n_attempts)
                + ' attempts'
            )

        # create new candidate
        try:
            start = next(candidates)
        except StopIteration:
            start = gen.integers(start_block, end_block)
        end = start + range_size
        candidate = (start, end)

        # check whether candidate is valid
        if candidate in ranges:
            continue
        if end > end_block:
            continue
        if non_overlapping:
            skip = False
            for other_start, other_end in ranges:
                if other_start <= end and other_end >= start:
                    skip = True
                    break
            if skip:
                continue

        ranges.add(candidate)

    # sort
    if sort:
        return sorted(ranges)
    else:
        ranges_list = list(ranges)
        gen.shuffle(ranges_list)
        return ranges_list

