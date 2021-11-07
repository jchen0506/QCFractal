from __future__ import annotations

import logging
import secrets
from typing import TYPE_CHECKING

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import select

from qcfractal.components.permissions.db_models import UserORM
from qcfractal.exceptions import AuthenticationFailure, UserManagementError
from qcfractal.portal.components.permissions import UserInfo, is_valid_password, is_valid_username

if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session
    from qcfractal.db_socket.socket import SQLAlchemySocket
    from typing import Optional, List, Dict, Any

    UserInfoDict = Dict[str, Any]


def _generate_password() -> str:
    """
    Generates a random password

    Returns
    -------
    :
        An plain-text random password.
    """
    return secrets.token_urlsafe(16)


def _hash_password(password: str) -> bytes:
    """
    Hashes a password in a consistent way
    """

    return bcrypt.hashpw(password.encode("UTF-8"), bcrypt.gensalt(6))


class UserSocket:
    def __init__(self, root_socket: SQLAlchemySocket):
        self.root_socket = root_socket
        self._logger = logging.getLogger(__name__)

    def _get_internal(self, session: Session, username: str, missing_ok: bool = False) -> Optional[UserORM]:
        """
        Obtain the ORM for a particular user.

        If the user is not found, an exception is raised. The ORM is attached to the given session

        Parameters
        ----------
        session
            SQLAlchemy session to use for querying
        username
            Username to search for

        Returns
        -------
        :
            ORM of the specified user
        """

        is_valid_username(username)
        stmt = select(UserORM).where(UserORM.username == username)
        user = session.execute(stmt).scalar_one_or_none()

        if missing_ok is False and user is None:
            raise UserManagementError(f"User {username} not found.")

        return user

    def list(self, *, session: Optional[Session] = None) -> List[UserInfoDict]:
        """
        Get information about all users

        Parameters
        ----------
        session
            An existing SQLAlchemy session to use. If None, one will be created
        """

        with self.root_socket.optional_session(session, True) as session:
            stmt = select(UserORM).order_by(UserORM.id.asc())
            all_users = session.execute(stmt).scalars().all()
            return [x.dict() for x in all_users]

    def get(self, username: str, *, session: Optional[Session] = None) -> UserInfoDict:
        """
        Obtains information for a user

        Returns all info for a user, except (hashed) password

        Parameters
        ----------
        username
            The username of the user
        session
            An existing SQLAlchemy session to use. If None, one will be created
        """

        with self.root_socket.optional_session(session, True) as session:
            user = self._get_internal(session, username)
            return user.dict()

    def get_permissions(self, username: str, *, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Obtain the permissions of a user.

        If the user does not exist, an exception is raised

        Parameters
        ----------
        username
            The username of the user
        session
            An existing SQLAlchemy session to use. If None, one will be created

        Returns
        -------
        :
            Dict of user permissions
        """

        with self.root_socket.optional_session(session, True) as session:
            user = self._get_internal(session, username)
            return user.role_obj.permissions

    def add(self, user_info: UserInfo, password: Optional[str] = None, *, session: Optional[Session] = None) -> str:
        """
        Adds a new user

        Parameters
        ----------
        user_info
            New user's information
        password
            The user's password. If None, a new password will be generated.
        session
            An existing SQLAlchemy session to use. If None, one will be created. If an existing session
            is used, it will be flushed before returning from this function.

        Returns
        -------
        :
            The password for the user. This is useful if the password is autogenerated
        """

        # Should have been checked already, but defense in depth
        is_valid_username(user_info.username)

        # ID should not be set
        if user_info.id is not None:
            raise UserManagementError("Cannot add a user - id was given as part of new user info")

        if password is None:
            password = _generate_password()

        is_valid_password(password)

        hashed_pw = _hash_password(password)

        # Role is not directly a part of the ORM
        user_dict = user_info.dict(exclude={"role"})

        try:
            with self.root_socket.optional_session(session) as session:
                # Will raise exception if role does not exist or role name is invalid
                role = self.root_socket.roles._get_internal(session, user_info.role)

                user = UserORM(**user_dict, role_id=role.id, password=hashed_pw)  # type: ignore
                session.add(user)
        except IntegrityError:
            raise UserManagementError(f"User {user_info.username} already exists")

        self._logger.info(f"User {user_info.username} added")
        return password

    def verify(self, username: str, password: str, *, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Verifies a given username and password, returning the users permissions.

        If the user is not found, or is disabled, or the password is incorrect, an exception is raised.

        Parameters
        ----------
        username
            The username of the user
        password
            The password associated with the username
        session
            An existing SQLAlchemy session to use. If None, one will be created

        Returns
        --------
        :
            The role and permissions available to that user.
        """

        is_valid_password(password)
        is_valid_username(username)

        with self.root_socket.optional_session(session, True) as session:
            try:
                user = self._get_internal(session, username)
            except UserManagementError as e:
                # Turn missing user into an Authentication error
                raise AuthenticationFailure("Incorrect username or password")

            if not user.enabled:
                raise AuthenticationFailure(f"User {username} is disabled.")

            try:
                pwcheck = bcrypt.checkpw(password.encode("UTF-8"), user.password)
            except Exception as e:
                self._logger.error(f"Password check failure for user {username}, error: {str(e)}")
                self._logger.error(
                    f"Error likely caused by encryption salt mismatch, potentially fixed by creating a new password for user {username}."
                )
                raise UserManagementError("Password decryption failure, please contact your system administrator.")

            if pwcheck is False:
                raise AuthenticationFailure("Incorrect username or password")

            return user.role_obj.permissions

    def modify(self, user_info: UserInfo, as_admin: bool, *, session: Optional[Session] = None) -> UserInfoDict:
        """
        Alters a user's information

        The user to modify is taken from the user_info object.

        The user's username or password cannot be changed this way. If `as_admin` is False, then only
        the descriptive changes (email, etc) can be changed. If it is True, then
        the `enabled` and `role` fields can also be changed.

        Parameters
        ----------
        user_info
            The user info to update the database with
        as_admin
            Enable changing sensitive columns (enabled & role)
        session
            An existing SQLAlchemy session to use. If None, one will be created. If an existing session
            is used, it will be flushed before returning from this function.

        Returns
        -------
        :
            An updated version of the user info, with all possible/allowed changes

        """

        with self.root_socket.optional_session(session) as session:
            user = self._get_internal(session, user_info.username)

            user.fullname = user_info.fullname
            user.organization = user_info.organization
            user.email = user_info.email

            if as_admin is True:
                role = self.root_socket.roles._get_internal(session, user_info.role)

                user.enabled = user_info.enabled
                user.role_id = role.id

            session.commit()

            self._logger.info(f"User {user_info.username} modified")

            return self.get(user_info.username, session=session)

    def change_password(self, username: str, password: Optional[str], *, session: Optional[Session] = None) -> str:
        """
        Alters a user's password

        Parameters
        ----------
        username
            The username of the user
        password
            The user's new password. If the password is empty, an exception is raised. If None, then a
            password will be generated
        session
            An existing SQLAlchemy session to use. If None, one will be created. If an existing session
            is used, it will be flushed before returning from this function.

        Returns
        -------
        :
            A string representing the password. If a new password was given, this should be identical
            to the input password. Otherwise, it will be the generated password.
        """

        if password is None:
            password = _generate_password()

        is_valid_password(password)

        with self.root_socket.optional_session(session) as session:
            user = self._get_internal(session, username)
            user.password = _hash_password(password)

        self._logger.info(f"Password for {username} modified")
        return password

    def delete(self, username: str, *, session: Optional[Session] = None) -> None:
        """Removes a user

        This will raise an exception if the user doesn't exist or is being referenced elsewhere in the
        database.

        Parameters
        ----------
        username
            The username of the user
        session
            An existing SQLAlchemy session to use. If None, one will be created. If an existing session
            is used, it will be flushed before returning from this function.
        """

        try:
            with self.root_socket.optional_session(session) as session:
                user = self._get_internal(session, username)
                session.delete(user)
        except IntegrityError:
            raise UserManagementError("User could not be deleted. Likely it is being referenced somewhere")

        self._logger.info(f"User {username} deleted")