from mongoengine.context_managers import switch_collection


def save_bar_data(self, datas: Sequence[BarData], collection_name: str = None):
  for d in datas:
      updates = self.to_update_param(d)
      updates.pop("set__gateway_name")
      updates.pop("set__vt_symbol")            
      if collection_name is None:
          (
              DbBarData.objects(
                  symbol=d.symbol, interval=d.interval.value, datetime=d.datetime
              ).update_one(upsert=True, **updates)
          )
      else:
          with switch_collection(DbBarData, collection_name):
              (
                  DbBarData.objects(
                      symbol=d.symbol, interval=d.interval.value, datetime=d.datetime
                  ).update_one(upsert=True, **updates)
              )


def save_tick_data(self, datas: Sequence[TickData], collection_name: str = None):
  for d in datas:
      updates = self.to_update_param(d)
      updates.pop("set__gateway_name")
      updates.pop("set__vt_symbol")
      if collection_name is None:
          (
              DbTickData.objects(
                  symbol=d.symbol, exchange=d.exchange.value, datetime=d.datetime
              ).update_one(upsert=True, **updates)
          )
      else:
          with switch_collection(DbTickData, collection_name):
              (
                  DbTickData.objects(
                      symbol=d.symbol, exchange=d.exchange.value, datetime=d.datetime
                  ).update_one(upsert=True, **updates)
              )