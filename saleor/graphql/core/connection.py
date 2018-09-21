import graphene
from graphene import Field, List, NonNull, ObjectType, String
from graphene_django import DjangoConnectionField
from graphene.relay.connection import Connection, PageInfo

# from cursor_pagination import CursorPaginator
from graphql_relay.connection.arrayconnection import connection_from_list_slice


class NonNullConnection(Connection):

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        super().__init_subclass_with_meta__(node=node, name=name, **options)

        # Override the original EdgeBase type to make to `node` field required.
        class EdgeBase(object):
            node = Field(
                cls._meta.node, description='The item at the end of the edge',
                required=True)
            cursor = String(
                required=True, description='A cursor for use in pagination')

        # Create the edge type using the new EdgeBase.
        edge_name = cls.Edge._meta.name
        edge_bases = (EdgeBase, ObjectType,)
        edge = type(edge_name, edge_bases, {})
        cls.Edge = edge

        # Override the `edges` field to make it non-null list
        # of non-null edges.
        cls._meta.fields['edges'] = Field(NonNull(List(NonNull(cls.Edge))))


class CountableConnection(NonNullConnection):
    class Meta:
        abstract = True

    total_count = graphene.Int(
        description='A total count of items in the collection')

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return root.length


class CursorConnectionField(DjangoConnectionField):

    @classmethod
    def resolve_connection(cls, connection, default_manager, args, iterable):
        if iterable is None:
            iterable = default_manager

        # if isinstance(iterable, QuerySet):
        #     if iterable is not default_manager:
        #         default_queryset = maybe_queryset(default_manager)
        #         iterable = cls.merge_querysets(default_queryset, iterable)
        #     _len = iterable.count()
        # else:
        #     _len = len(iterable)
        _len = iterable.count()
        connection = connection_from_list_slice(
            iterable,
            args,
            slice_start=0,
            list_length=_len,
            list_slice_length=_len,
            connection_type=connection,
            edge_type=connection.Edge,
            pageinfo_type=PageInfo,
        )
        connection.iterable = iterable
        connection.length = _len
        return connection

        # connection = cursor_pagination_connection(
        #     iterable, args, connection_type=connection,
        #     edge_type=connection.Edge, pageinfo_type=PageInfo)
        # return connection


# def cursor_pagination_connection(
#         qs, args, connection_type, edge_type, pageinfo_type):
#     args = args or {}

#     before = args.get('before')
#     after = args.get('after')
#     first = args.get('first')
#     last = args.get('last')

#     paginator = CursorPaginator(qs, ordering=('pk',))
#     page = paginator.page(first, last, after, before)

#     edges = [
#         edge_type(node=node, cursor=paginator.cursor(node)) for node in page]

#     first_edge_cursor = edges[0].cursor if edges else None
#     last_edge_cursor = edges[-1].cursor if edges else None

#     connection = connection_type(
#         edges=edges,
#         page_info=pageinfo_type(
#             start_cursor=first_edge_cursor,
#             end_cursor=last_edge_cursor,
#             has_previous_page=page.has_previous,
#             has_next_page=page.has_next))
#     return connection
