import cmdc


def test_pass_apikey_updates_headers():
    c = cmdc.Client(apikey="foobar")
    assert "apikey" in c.sess.headers
    assert c.sess.headers["apikey"] == "foobar"
