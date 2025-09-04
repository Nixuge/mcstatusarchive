from dataclasses import dataclass


@dataclass
class JavaLoadingSteps:
    dns: bool
    db: bool

    def all_done(self):
        if self.dns and self.db:
            return True
        if not self.dns:
            return "DNS"
        if not self.db:
            return "DB"

    @classmethod
    def new(cls):
        return cls(False, False)