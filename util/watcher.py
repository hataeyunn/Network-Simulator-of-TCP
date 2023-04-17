from collections.abc import MutableSequence

class CallbackList(MutableSequence):
    def __init__(self, *args, callback=None, **kwargs):
        self._list = list(*args, **kwargs)
        self._callback = callback

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self._list[index] = value
        if self._callback:
            self._callback(self)

    def __delitem__(self, index):
        del self._list[index]
        if self._callback:
            self._callback(self)

    def __len__(self):
        return len(self._list)

    def insert(self, index, value):
        self._list.insert(index, value)
        if self._callback:
            self._callback(self)

    # 콜백 함수 정의 (buffer sequence_num으로 정렬)
    def my_callback(self):
        self._list.sort(key=lambda x: x.header['squence_num'])
