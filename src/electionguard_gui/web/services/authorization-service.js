export default {
  async getUserId() {
    const result = await eel.get_user_id()();
    return result;
  },
  async setUserId(id) {
    await eel.set_user_id(id)();
  },
};
