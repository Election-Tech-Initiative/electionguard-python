export default {
  _userId: undefined,
  _isAdmin: undefined,
  async getUserId() {
    if (!this._userId) {
      this._userId = await eel.get_user_id()();
    }
    return this._userId;
  },
  async setUserId(id) {
    await eel.set_user_id(id)();
    this._userId = id;
  },
  async isAdmin() {
    if (!this._isAdmin) {
      this._isAdmin = await eel.is_admin()();
    }
    return this._isAdmin;
  },
};
