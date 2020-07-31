import covidcountydata as ccd


def test_pass_apikey_updates_headers():
    c = ccd.Client(apikey="foobar")
    assert "apikey" in c.sess.headers
    assert c.sess.headers["apikey"] == "foobar"
