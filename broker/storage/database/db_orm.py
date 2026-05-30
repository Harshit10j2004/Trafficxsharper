from sqlalchemy import create_engine,Column, Integer, String, Float, JSON, TEXT,DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from broker.setting.conifg import settings


engine = create_engine(settings.DB_LINK)
Base = declarative_base()


class ClientInfo(Base):
    __tablename__ = 'client_info'

    client_id = Column(Integer, primary_key=True,autoincrement=True)

    client_name = Column(String)
    thresold = Column(Integer)
    l_buff = Column(Integer)
    h_buff = Column(Integer)
    email = Column(String)

    ami = Column(JSON)
    server_type = Column(JSON)
    security_group = Column(JSON)

    manager_ip = Column(String)
    joining_token = Column(String)


class SystemInfo(Base):
    __tablename__ = 'system_info'

    id = Column(Integer, primary_key=True, autoincrement=True)


    last_scale_up_time = Column(DateTime)
    last_scale_down_time = Column(DateTime)

    total_cpu_window = Column(Integer)
    total_cur_fluc = Column(Integer)
    total_cur_ml_window = Column(Integer)
    total_cur_queue = Column(Float)
    total_cur_rps = Column(Float)
    last_queue = Column(Float)
    last_rps = Column(Float)
    last_cpu = Column(Float)
    last_ml_window = Column(Float)

    client_id = Column(Integer)


Session = sessionmaker(bind=engine)
session = Session()

class Add_data():


    @staticmethod
    def update1(total_cur_queue,last_queue,total_cur_rps,last_rps,last_cpu,client_id):

        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.total_cur_queue: total_cur_queue,
                SystemInfo.last_queue: last_queue,
                SystemInfo.total_cur_rps: total_cur_rps,
                SystemInfo.last_rps: last_rps,
                SystemInfo.last_cpu: last_cpu
            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()


    @staticmethod
    def update2(total_cur_queue, total_cur_rps, client_id):

        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.total_cur_queue: total_cur_queue,
                SystemInfo.total_cur_rps: total_cur_rps,

            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()


    @staticmethod
    def update3(total_cpu_window, client_id):
        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.total_cpu_window: total_cpu_window,

            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()

    @staticmethod
    def update4(total_cur_fluc, client_id):
        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.total_cur_fluc: total_cur_fluc,

            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()

    @staticmethod
    def update5(total_cpu_window, total_cur_ml_window, client_id):
        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.total_cpu_window: total_cpu_window,
                SystemInfo.total_cur_ml_window: total_cur_ml_window

            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()

    @staticmethod
    def update6(last_scale_up_time, client_id):
        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.last_scale_up_time: last_scale_up_time,

            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()

    @staticmethod
    def update7(total_cur_ml_window, last_ml_window,  client_id):
        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.total_cur_ml_window: total_cur_ml_window,
                SystemInfo.last_ml_window: last_ml_window,

            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()

    @staticmethod
    def update8(total_cpu_window, total_cur_ml_window, client_id):
        try:
            session.query(SystemInfo).filter(
                SystemInfo.client_id == client_id
            ).update({
                SystemInfo.total_cur_ml_window: total_cur_ml_window,
                SystemInfo.total_cpu_window: total_cpu_window,

            })
            session.commit()
            return True

        except Exception as e:

            session.rollback()
            raise e

        finally:
            session.close()


class Retrive():

    @staticmethod
    def retrive_data_clint_info(client_id):

        result = session.query(
            ClientInfo.client_name,
            ClientInfo.thresold,
            ClientInfo.l_buff,
            ClientInfo.h_buff,
            ClientInfo.email,
            ClientInfo.ami,
            ClientInfo.server_type,
            ClientInfo.security_group,
            ClientInfo.manager_ip,
            ClientInfo.joining_token
        ).filter(
            ClientInfo.client_id == client_id
        ).first()

        return result

    @staticmethod
    def retrive_data_system_info(client_id):


        result = session.query(
            SystemInfo.last_scale_up_time,
            SystemInfo.last_scale_down_time,
            SystemInfo.total_cpu_window,
            SystemInfo.total_cur_fluc,
            SystemInfo.total_cur_ml_window,
            SystemInfo.total_cur_queue,
            SystemInfo.total_cur_rps,
            SystemInfo.last_queue,
            SystemInfo.last_rps,
            SystemInfo.last_cpu,
            SystemInfo.last_ml_window
        ).filter(
            SystemInfo.client_id == client_id
        ).first()

        return result






