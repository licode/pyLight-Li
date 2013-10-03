from main.models import User, History
import logging
log = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self, user):
        self.user = user
    def get_current_history(self):
        try:
            histories = History.objects.filter(user=self.user).filter(is_current=True)
        except:
            return None
        if len(histories) == 0:
            return History.objects.create(name="Demo", user=self.user, size=0, is_current=True)
        assert(len(histories) == 1)
        print "return history"
        return histories[0]