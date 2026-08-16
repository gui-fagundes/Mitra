from sqlalchemy import inspect


class ToDictMixin:
    def to_dict(self, include_unset: bool = False):
        data = {}

        for c in inspect(self).mapper.column_attrs:
            value = getattr(self, c.key)
            if include_unset or value is not None:
                data[c.key] = value

        for rel in inspect(self).mapper.relationships:
            related_object = getattr(self, rel.key)
            if related_object is not None:
                if isinstance(related_object, list):
                    data[rel.key] = [r.to_dict(include_unset) for r in related_object]
                else:
                    data[rel.key] = related_object.to_dict(include_unset)

        return data
