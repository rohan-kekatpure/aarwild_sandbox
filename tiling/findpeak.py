def findpeak(lst):
    N = len(lst)
    high = N - 1
    low = 0
    mid = 0
    while low < high:
        mid = (low + high) // 2
        if (mid == 0) or (mid == N - 1):
            return lst[mid]

        left_elem = lst[mid - 1]
        right_elem = lst[mid + 1]
        mid_elem = lst[mid]

        if left_elem < mid_elem > right_elem:
            return mid_elem

        if left_elem <= mid_elem <= right_elem:
            low = mid
        elif left_elem >= mid_elem >= right_elem:
            high = mid

    return lst[mid]

def main():
    lst = [1, 2, 1, 3, 4, 5]
    print(findpeak(lst))

if __name__ == '__main__':
    main()
