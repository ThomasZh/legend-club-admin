/**
 * 活动详情交互脚本
 * @2016/05/25
 */
$(function(){

  var activityID = $('#data-actID').html();
  var articleID = $('#data-atcID').html();
  // console.log('article: '+articleID);

  function createAvatar(item){
    var imgURL = '/static/img/icon/avatar_no_blue.png';
    if(item.account_avatar) {
        imgURL = item.account_avatar;
    }
    var span = '';
        span +='<span class="ui-avatar-tiled margin-right-4">';
        span +='  <span style="background-image:url('+imgURL+')"></span>';
        span +='</span>';

    return span;
  }

  //先获取参加成员名单
  $.getJSON('/customer/activity/members?id='+activityID, function(result){

    console.log(result);
    var amount = '暂时无';
    if(result.length) amount = result.length;
    $('.act-mbr-num').html(amount);

    if(!result.length) {
      $('.view-all-mbrs').hide();
      return;
    }

    // TODO: 动态创建头像
    /**
     * <span class="ui-avatar-tiled margin-right-4">
       <span style="background-image:url(/static/img/icon/avatar_no_blue.png)"></span>
     </span>
     */
    var members = '';
    for(var i in result){
      members += createAvatar(result[i]);
    }
    $('.members-avatar').html(members);

  });//成员处理完毕

  // 再获取活动路线详情
  // 活动内容可能为空，所以要判断下
  // @2016/06/06
  if(articleID){
    $.getJSON('/customer/activity/article?id='+articleID, function(result){
      // console.log(result);
      var paragraphs = '';
      for(var i in result){
        var p = result[i];
        if(p.type=='heading'){//标题
          paragraphs += '<span class="bm">'+p.content+'</span>';
        }
        if(p.type=='img'){//图片
          paragraphs += '<div class="m1">';
          paragraphs += ' <img src="'+p.content+'">';
          paragraphs += '</div>';
        }
        if(p.type=='raw'){//文本
          paragraphs += '<div class="m1">';
          paragraphs +=   p.content;
          paragraphs += '</div>';
        }
      }
      // 添加到页面
      $('.routines').html(paragraphs);
      $('.ui-loading-wrap').addClass('hidden');//隐藏进度条
    });
  }else{
    $('.ui-loading-wrap').addClass('hidden');//隐藏进度条
  }


  $('.join-wexin-group').click(function(){
    location.href = '/bike-forever/wechat/activity/qrcode?id='+activityID;
  })

  $('.join-activity').click(function(){
    var phase = document.getElementById('phase').value;
    // 这个是jquery用法 @2016/06/13
    // var phase = $('#phase').val();
    // 报名中 or 已成行
    if (phase == "0" || phase == "1") {
      location.href = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxaa328c83d3132bfb&redirect_uri=http://planc2c.com/bike-forever/wechat/activity/apply/step1?id='+activityID+'&response_type=code&scope=snsapi_userinfo&state=1#wechat_redirect';
    }
    //    var logined = document.getElementById('logined').value;
    //    if (logined == true) {
    //      location.href = '/bike-forever/wechat/apply/step1?id='+activityID;
    //    } else {
    //      location.href = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxaa328c83d3132bfb&redirect_uri=http://planc2c.com/bike-forever/wechat/activity/apply/step1?id='+activityID+'&response_type=code&scope=snsapi_userinfo&state=1#wechat_redirect';
    //    }
  });

});
